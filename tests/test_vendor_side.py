import json
import time

import pytest

from surya import handler, market


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.delenv("MARKET_TABLE", raising=False)
    monkeypatch.delenv("KNOWLEDGE_TABLE", raising=False)
    market._mem.clear()
    yield
    market._mem.clear()


def api(method, path, body=None, params=None):
    r = handler.lambda_handler({"requestContext": {"http": {"method": method}}, "rawPath": path,
                                "body": json.dumps(body) if body is not None else None, "queryStringParameters": params}, None)
    return r["statusCode"], json.loads(r["body"])


GOOD = {"total_price_rs": 189000, "system_kw": 3, "dcr": "yes", "gst_included": "yes", "module_watt": 550, "module_count": 6,
        "inverter_kw": 3, "module_performance_warranty_years": 25, "inverter_warranty_years": 8, "system_warranty_years": 5,
        "advance_pct": 20, "timeline_days": 20, "net_meter_included": "yes", "structure_included": "yes", "earthing_included": "yes"}


def test_vendors_see_open_requests_without_the_household():
    rid = api("POST", "/market/requests", {"state": "DL", "kw": 3, "pincode": "110075"})[1]["request"]["id"]
    code, data = api("GET", "/market/open", params={"state": "DL"})
    assert code == 200
    req = next(r for r in data["requests"] if r["id"] == rid)
    assert req["area"] == "110xxx" and req["kw"] == 3
    assert "wa_id" not in json.dumps(data) and "110075" not in json.dumps(data)


def test_a_real_vendor_quote_joins_the_comparison_and_builds_a_scorecard():
    rid = api("POST", "/market/requests", {"state": "DL", "kw": 3})[1]["request"]["id"]
    code, data = api("POST", f"/market/requests/{rid}/quotes", {"vendor_name": "Sunrise Rooftops Pvt Ltd", "quote": GOOD})
    assert code == 201 and data["check"]["verdict"] == "ok" and data["vendor"]["demo"] is False
    view = market.view(rid, now=time.time() + 60)
    real = next(q for q in view["quotes"] if not q["vendor"]["demo"])
    assert real["vendor"]["name"] == "Sunrise Rooftops Pvt Ltd" and real["vendor"]["scorecard"]["quotes_sent"] == 1
    assert any(v["name"] == "Sunrise Rooftops Pvt Ltd" for v in market.vendors_for("DL"))
    open_ = api("GET", "/market/open", params={"state": "DL", "vendor": "Sunrise Rooftops Pvt Ltd"})[1]["requests"]
    assert next(r for r in open_ if r["id"] == rid)["you_quoted"] is True


def test_vendors_cannot_impersonate_demo_vendors_or_send_broken_quotes():
    rid = api("POST", "/market/requests", {"state": "DL", "kw": 3})[1]["request"]["id"]
    assert api("POST", f"/market/requests/{rid}/quotes", {"vendor_name": "Dhoop Rooftop Co.", "quote": GOOD})[0] == 400
    assert api("POST", f"/market/requests/{rid}/quotes", {"vendor_name": "Real Co", "quote": {"system_kw": 3}})[0] == 400
    assert api("POST", f"/market/requests/{rid}/quotes", {"vendor_name": "Real Co"})[0] == 400
    assert api("POST", "/market/requests/nope/quotes", {"vendor_name": "Real Co", "quote": GOOD})[0] == 404


def test_website_samples_stay_out_of_the_way_of_real_requests():
    for _ in range(3):
        api("POST", "/market/requests", {"state": "UP", "kw": 3, "sample": True})
    data = api("GET", "/market/open", params={"state": "UP"})[1]["requests"]
    assert len(data) == 1 and data[0]["sample"]  # nothing real yet: one labelled sample to try
    rid = api("POST", "/market/requests", {"state": "UP", "kw": 4, "pincode": "226010"})[1]["request"]["id"]
    data = api("GET", "/market/open", params={"state": "UP"})[1]["requests"]
    assert [r["id"] for r in data] == [rid] and not data[0]["sample"]


def test_requests_stored_before_the_flag_count_as_samples_unless_from_whatsapp():
    def legacy(wa_id):
        rid = market.create_request({"state": "HR", "kw": 3}, wa_id=wa_id)["request"]["id"]
        meta = json.loads(market._mem[f"REQ#{rid}"]["META"]["data"])
        del meta["sample"]
        market._mem[f"REQ#{rid}"]["META"]["data"] = json.dumps(meta)
        return rid
    legacy(None)
    rid = legacy("whatsapp:+910000000000")
    rows = market.open_requests("HR")
    assert [r["id"] for r in rows] == [rid] and not rows[0]["sample"]
