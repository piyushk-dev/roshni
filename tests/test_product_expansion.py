import base64
import json
import time

import pytest

from surya import bot, handler, knowledge, market, product, scam


@pytest.fixture(autouse=True)
def clean_market(monkeypatch):
    monkeypatch.delenv("MARKET_TABLE", raising=False)
    monkeypatch.delenv("KNOWLEDGE_TABLE", raising=False)
    market._mem.clear()
    yield
    market._mem.clear()


def api(method, path, body=None, params=None):
    response = handler.lambda_handler({"requestContext": {"http": {"method": method}}, "rawPath": path,
        "body": json.dumps(body) if body is not None else None, "queryStringParameters": params}, None)
    return response["statusCode"], json.loads(response["body"])


def ready(mode="sample", state="DL", wa_id=None):
    result = market.create_request({"state": state, "kw": 3, "mode": mode, "pincode": "110001"}, wa_id=wa_id)
    return market.view(result["request"]["id"], now=time.time()+20)


def test_regions_are_complete_and_special_rate_is_consistent():
    catalog = product.schemes("AS", 3)
    assert len(catalog["states"]) == 36
    assert catalog["central_rs"] == 85800
    assert [s["id"] for s in catalog["schemes"] if s["kind"] == "central"] == ["special"]
    assert product.schemes("TN", 3)["central_rs"] == 78000
    assert "19,800" in next(s for s in catalog["schemes"] if s["id"] == "society")["amount"]["en"]
    assert not product.schemes("TN")["topup_reviewed"]


@pytest.mark.parametrize("state", ["XX", "DELHI", "", "ZZ"])
def test_invalid_state_is_rejected(state):
    with pytest.raises(ValueError):
        product.schemes(state)


def test_unconfirmed_and_non_dcr_never_enter_the_budget():
    assert product.schemes("DL", 3, "no")["potential_central_rs"] == 0
    assert product.schemes("DL", 3, "not_stated")["central_rs"] == 0
    assert product.finance({"dcr": "not_stated"})["central_prepayment_rs"] == 0
    assert product.finance({"dcr": "no"})["central_prepayment_rs"] == 0


def test_state_topups_are_sourced_and_never_summed_automatically():
    catalog = product.schemes("DL", 2)
    topup = next(s for s in catalog["schemes"] if s["id"] == "dl-topup")
    assert topup["calc"]["per_kw"] == 26000
    assert "solar.delhi.gov.in/page/state-subsidy" in topup["source"]
    assert catalog["state_topup_included_rs"] == 0
    assert "upneda.org.in" in next(s for s in product.schemes("UP")["schemes"] if s["id"] == "up-topup")["source"]


def test_longer_wait_requires_more_cash_and_interest():
    quick = product.finance({"dcr": "yes", "delay_months": 1})
    slow = product.finance({"dcr": "yes", "delay_months": 6})
    assert quick["cash_before_install_rs"] == 19500
    assert slow["cash_during_wait_rs"] > quick["cash_during_wait_rs"]
    assert slow["interest_during_wait_rs"] > quick["interest_during_wait_rs"]
    assert slow["emi_after_rs"] < slow["emi_before_rs"]
    assert "recasting" in slow["note"]["en"]


def test_zero_interest_and_full_own_contribution_work():
    zero = product.finance({"cost_rs": 120000, "margin_pct": 10, "rate_pct": 0, "years": 1, "dcr": "no"})
    assert zero["emi_before_rs"] == 9000
    assert zero["interest_during_wait_rs"] == 0
    cash = product.finance({"margin_pct": 100})
    assert cash["emi_before_rs"] == cash["emi_after_rs"] == 0


def test_prepayment_never_exceeds_balance_after_wait():
    paid = product.finance({"cost_rs": 120000, "dcr": "yes", "years": 1, "rate_pct": 0, "delay_months": 12})
    assert paid["potential_central_rs"] == 78000
    assert paid["central_prepayment_rs"] == paid["emi_after_rs"] == 0
    almost = product.finance({"cost_rs": 120000, "dcr": "yes", "years": 1, "rate_pct": 0, "delay_months": 11})
    assert almost["central_prepayment_rs"] == 9000
    assert almost["emi_after_rs"] == 0


def test_assam_uses_government_source_and_secondary_rules_stay_identified():
    assam = next(s for s in product.schemes("AS")["schemes"] if s["id"] == "as-topup")
    assert assam["official"] and "apdcl.org" in assam["source"]
    assert assam["calc"]["conditional"]
    assert "Confirm current" in assam["how"]["en"]
    rajasthan = next(s for s in product.schemes("RJ")["schemes"] if s["id"] == "rj-topup")
    assert not rajasthan["official"]


def test_completed_period_uses_indian_calendar_and_threshold_is_not_rounded(monkeypatch):
    from datetime import date
    monkeypatch.setattr(product, "today_india", lambda: date(2026, 10, 1))
    assert product.care({"month":"2026-09", "actual_kwh":358.4, "promised_kwh":400})["status"] == "review"
    with pytest.raises(ValueError):
        product.care({"month":"2026-10", "actual_kwh":100, "promised_kwh":400})


@pytest.mark.parametrize("field,value", [("kw",float("nan")),("cost_rs",float("inf")),("margin_pct",-1),("years",1.5),("delay_months",13)])
def test_budget_rejects_unusable_inputs(field, value):
    with pytest.raises(ValueError):
        product.finance({field: value})


def test_real_profiles_have_no_invented_outcomes_or_registration_badge():
    vendors = market.vendors_for("DL")
    assert {v["name"] for v in vendors} == {"SolarSquare", "Alien Energy", "Bridgeway Power", "Tata Power Solaroof"}
    assert all(not v["verified"] and v["source"].startswith("https://") for v in vendors)
    assert all("scorecard" not in v for v in vendors)
    assert market.vendors_for("TS")[0]["name"] == "Freyr Energy"
    assert market.vendors_for("TN")[0]["name"] == "Tata Power Solaroof"
    assert "not guaranteed" in market.vendors_for("TN")[0]["coverage_note"]["en"]
    comparison = ready()
    assert comparison["recommendation"] is None  # cannot endorse a real business on fabricated terms
    assert all(q["check"]["verdict"] == "ok" for q in comparison["quotes"])
    assert all(not q["vendor"]["scorecard"]["outcomes_available"] for q in comparison["quotes"])


def test_educational_risks_are_anonymous_and_recommended_by_terms():
    comparison = ready("traps")
    assert len(comparison["quotes"]) == 4
    assert all(q["vendor"]["name"].startswith("Example quote") for q in comparison["quotes"])
    assert any(q["check"]["verdict"] == "red" for q in comparison["quotes"])
    assert comparison["recommendation"]["cheapest_is_trap"]


def test_samples_do_not_train_prices_or_increment_real_impact(monkeypatch):
    seen = []
    monkeypatch.setattr(knowledge, "count", lambda **kw: seen.append(kw))
    ready()
    assert seen == []


@pytest.mark.parametrize("pin", ["000001", "abc110001", "11000199", "12"])
def test_pin_is_not_silently_rewritten(pin):
    assert api("POST", "/market/requests", {"pincode": pin})[0] == 400


def test_request_ids_are_unguessable_and_phone_stays_private():
    view = ready(wa_id="test-phone")
    assert len(view["request"]["id"]) == 32
    assert "test-phone" not in json.dumps(view)


def test_cannot_choose_a_quote_before_it_is_visible():
    result = market.create_request({})
    with pytest.raises(ValueError):
        market.choose(result["request"]["id"], "solarsquare")


def test_choose_saves_preference_without_claiming_contact_shared(monkeypatch):
    comparison = ready()
    monkeypatch.setattr(market.time, "time", lambda: comparison["quotes"][-1]["ready_at"]+1)
    chosen = market.choose(comparison["request"]["id"], "solarsquare")
    assert chosen["contact_shared"] is False
    assert "No installer was contacted" in market.wa_chosen(chosen, "en")
    assert ".." not in market.wa_chosen(chosen, "en").splitlines()[0]


def test_expiry_and_deletion_remove_request_and_group_interest(monkeypatch):
    view = ready(wa_id="test-phone")
    rid = view["request"]["id"]
    assert market.group("DL", "110001")["homes"] == 1
    market.forget_user("test-phone")
    with pytest.raises(KeyError):
        market.view(rid)
    assert market.group("DL", "110001")["homes"] == 0
    other = ready()
    real_now = time.time()
    monkeypatch.setattr(market.time, "time", lambda: real_now+31*86400)
    with pytest.raises(KeyError):
        market.view(other["request"]["id"])


def test_missing_gst_or_advance_is_not_presented_as_zero():
    q = market.clean_quote({"total_price_rs":195000,"system_kw":3,"dcr":"yes"}, "Written quote", "DL")
    checked = market.assess(q, knowledge.price_band("DL",3))
    assert checked["gst_unknown"]
    assert checked["pay_upfront_rs"] is None


def test_generation_uses_same_full_month_and_zero_actual_is_a_real_reading():
    result = product.care({"month":"2026-01","actual_kwh":0,"promised_kwh":400,"kw":3})
    assert result["pct"] == 0 and result["status"] == "review"
    assert "2026-01" in result["draft"]["en"]
    assert "weather" in result["next"]["en"]
    assert result["cleaning_review"]


@pytest.mark.parametrize("month", ["2026-13", "garbage", "2999-01"])
def test_care_rejects_bad_or_future_period(month):
    assert api("POST", "/care/check", {"month":month,"actual_kwh":10,"promised_kwh":20})[0] == 400


def test_export_is_not_generation_and_bill_mismatch_is_not_a_refund():
    result = product.bill_balance({"generation_kwh":400,"import_kwh":300,"export_kwh":150,"bill_export_kwh":100})
    assert result["self_consumed_kwh"] == 250
    assert result["household_use_kwh"] == 550
    assert result["net_grid_kwh"] == 150
    assert result["export_difference_kwh"] == 50
    assert "not an automatic refund" in result["note"]["en"]
    extra = product.bill_balance({"generation_kwh":400,"import_kwh":300,"export_kwh":150,"bill_export_kwh":200})
    assert extra["meter_bill_difference_kwh"] == -50 and extra["status"] == "review"
    with pytest.raises(ValueError):
        product.bill_balance({"generation_kwh":100,"import_kwh":10,"export_kwh":101,"bill_export_kwh":10})


def test_scam_check_finds_pressure_fee_otp_and_fake_portal():
    flags = scam.check("Government authorised solar agent! Today only pay ₹999 processing fee, send OTP, 60% advance at pmsuryaghar-offer.com")
    assert {"fee","otp","lookalike","advance","urgency"} <= {f["code"] for f in flags}
    assert scam.verdict(flags) == "red"
    assert "does not verify" in scam.render([],"en")["title"]


def test_protective_advice_is_not_misread_as_a_scam_request():
    assert not {"otp","fee"} & {f["code"] for f in scam.check("Never share OTP. No processing fee. Apply at pmsuryaghar.gov.in.")}


def test_json_and_base64_validation_are_consistent():
    assert api("POST","/scam-check",[])[0] == 400
    event = {"requestContext":{"http":{"method":"POST"}},"rawPath":"/scam-check",
             "isBase64Encoded":True,"body":base64.b64encode(b'{"text":"solar offer with OTP"}').decode()}
    assert handler.lambda_handler(event,None)["statusCode"] == 200
    event["body"] = "!!!"
    assert handler.lambda_handler(event,None)["statusCode"] == 400


def test_http_create_view_choose_delete_and_preview(monkeypatch):
    code,data=api("POST","/market/requests",{"mode":"traps","state":"DL"})
    assert code == 201
    rid=data["request"]["id"]
    now=time.time()
    monkeypatch.setattr(market.time,"time",lambda:now+20)
    assert len(api("GET",f"/market/requests/{rid}")[1]["quotes"]) == 4
    assert api("POST",f"/market/requests/{rid}/choose",{"vendor_id":"example-1"})[0] == 200
    assert api("DELETE",f"/market/requests/{rid}")[0] == 200
    assert api("GET",f"/market/requests/{rid}")[0] == 404
    assert api("POST","/market/preview",{"quote":{"total_price_rs":195000,"system_kw":3}})[1]["check"]["subsidy_rs"] == 0


def test_new_read_only_endpoints_and_empty_offer_errors():
    assert api("GET","/vendors",params={"state":"DL"})[0] == 200
    assert api("GET","/schemes",params={"state":"AS"})[1]["central_rs"] == 85800
    checklist=api("GET","/care/checklists")[1]
    assert len(checklist["groups"]) == 2
    assert any("serial" in i["text"]["en"] for g in checklist["groups"] for i in g["items"])
    assert api("POST","/scam-check",{"text":""})[0] == 400


def test_whatsapp_market_passport_schemes_and_deletion(monkeypatch):
    class WA:
        def __init__(self): self.sent=[]
        def mark_read(self, _): pass
        def send_text(self, _, text): self.sent.append(text)
    wa=WA()
    def send(text,user):
        return bot.handle({"from":"test-phone","id":"test-id","type":"text","text":{"body":text}},user,wa,None)
    user={"lang":"en","last":{"kw":3,"state":"DL"}}
    user=send("QUOTES",user)
    assert user["asking_pin"]
    user=send("110001",user)
    assert user["market_request"]
    assert "not installer offers" in wa.sent[-1]
    send("PASSPORT",user)
    assert "outages" in wa.sent[-1]
    send("SCHEMES AS",user)
    assert "85,800" in wa.sent[-1]
    rid=user["market_request"]
    assert send("DELETE MY DATA",user) is None
    with pytest.raises(KeyError): market.view(rid)
