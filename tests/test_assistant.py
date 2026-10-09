import json

import pytest

from surya import handler, places, qa

LUCKNOW = {"name": "Lucknow, Uttar Pradesh, India", "state": "UP", "lat": 26.8547, "lon": 80.9214}


class Bedrock:
    """Replays a script of Converse replies and keeps what it was sent."""

    def __init__(self, *replies):
        self.replies, self.sent = list(replies), []

    def converse(self, **request):
        self.sent.append(json.loads(json.dumps(request, default=str)))
        return self.replies.pop(0)


def tool_use(name, args, tid="t1", thinking="<thinking>I need the tool.</thinking>"):
    return {"stopReason": "tool_use", "output": {"message": {"role": "assistant", "content": [
        {"text": thinking}, {"toolUse": {"toolUseId": tid, "name": name, "input": args}}]}}}


def final(text):
    return {"stopReason": "end_turn", "output": {"message": {"role": "assistant", "content": [{"text": text}]}}}


def tool_results(request):
    return [c["toolResult"] for m in request["messages"] for c in m["content"] if "toolResult" in c]


@pytest.fixture(autouse=True)
def lucknow(monkeypatch):
    places._cache.clear()
    monkeypatch.setattr(places, "_geocode", lambda text, client=None: dict(LUCKNOW) if "lucknow" in text.lower() else None)
    monkeypatch.delenv("KNOWLEDGE_TABLE", raising=False)


def test_a_subsidy_question_is_answered_from_the_scheme_list():
    b = Bedrock(tool_use("schemes_for", {"place": "Lucknow", "system_kw": 3}),
                final("<thinking>UP pays a top-up.</thinking>You can get ₹78,000 from the centre and up to ₹30,000 from UP."))
    out = qa.answer_full("Lucknow mein 3 kW par kitni subsidy milegi?", {}, "en", client=b)
    assert out["text"] == "You can get ₹78,000 from the centre and up to ₹30,000 from UP."
    assert out["used"] == [{"en": "the scheme list for Uttar Pradesh", "hi": "उत्तर प्रदेश की योजना सूची"}]
    result = tool_results(b.sent[1])[0]["content"][0]["json"]
    assert result["central_subsidy"] == "₹78,000" and "15,000" in result["state_help"][0]["rule"]
    # the cap is applied for the model: ₹15,000/kW for 3 kW would be ₹45,000, but UP pays at most ₹30,000
    assert result["state_help"][0]["for_this_size"] == "₹30,000" and result["together_if_eligible_for_both"] == "₹1,08,000"
    assert b.sent[0]["toolConfig"]["tools"][0]["toolSpec"]["name"] == "schemes_for"


def test_rough_estimate_from_a_typed_bill():
    out, label = qa.rough_estimate("Lucknow", monthly_bill_rs=3000)
    assert out["monthly_units"] == 429 and "assumed" in out["units_basis"]
    assert out["system_kw"] == 3.5 and out["central_subsidy"] == "₹78,000"
    assert out["typical_cost"] == "₹2,03,000" and out["cost_after_central_subsidy"] == "₹1,25,000"  # ₹58,000/kW above 3 kW
    assert out["state_top_up_if_eligible"] == "₹30,000" and 3 < out["payback_years"] < 6
    assert "rough" in label["en"]


def test_a_flat_conditional_state_top_up_is_passed_on_with_its_conditions():
    out, _ = qa.rough_estimate("Jaipur, Rajasthan", monthly_units=300)
    assert out["state_top_up_if_eligible"] == "₹17,000"
    assert "Nishulk Bijli" in out["state_help"][0]["who"]


def test_delhi_homes_under_200_units_are_warned():
    out, _ = qa.rough_estimate("Delhi", monthly_units=180)
    assert out["system_kw"] == 1.5 and "200 units" in out["notes"][0]


def test_a_place_it_cannot_find_goes_back_to_the_model_as_an_error():
    b = Bedrock(tool_use("dust_forecast", {"place": "Atlantis"}), final("Which state do you live in?"))
    out = qa.answer_full("When should I clean my panels in Atlantis?", {}, "en", client=b)
    result = tool_results(b.sent[1])[0]
    assert result["status"] == "error" and "state" in result["content"][0]["json"]["error"]
    assert out == {"text": "Which state do you live in?", "used": []}


def test_the_scam_check_and_the_application_step_are_tools_too():
    b = Bedrock(tool_use("check_offer", {"text": "Pay ₹2,000 registration fee and share the OTP for free solar"}, "a"),
                tool_use("application_status", {}, "b"), final("Don't pay. Your application is at step 6."))
    out = qa.answer_full("Is this real? Also where is my application?", {"journey": {"stage": 5, "since": 0}}, "en", client=b)
    offer = tool_results(b.sent[1])[0]["content"][0]["json"]
    step = tool_results(b.sent[2])[1]["content"][0]["json"]
    assert offer["verdict"] == "red" and len(offer["signs"]) >= 2
    assert step["step"] == 6 and step["title"] == "Net meter and inspection"
    assert [u["en"] for u in out["used"]] == ["the scam check", "your application's step"]


def test_endless_tool_calls_end_in_the_helpline_fallback():
    b = Bedrock(*[tool_use("application_status", {}, str(i)) for i in range(qa.MAX_TURNS)])
    out = qa.answer_full("?", {}, "hi", client=b)
    assert "15555" in out["text"] and len(b.sent) == qa.MAX_TURNS


def test_states_are_found_by_name_code_or_hindi_without_the_geocoder(monkeypatch):
    def down(text, client=None):
        raise RuntimeError("no geo-places in this SDK")
    monkeypatch.setattr(places, "_geocode", down)
    assert places.state_in("Goalpara, Assam") == "AS"  # whole words: not Goa
    assert places.state_in("UP") == "UP" and places.state_in("उत्तर प्रदेश में") == "UP"
    assert places.find("Jaipur, Rajasthan")["state"] == "RJ"
    assert places.find("Atlantis") is None


def test_places_route_finds_a_place_or_says_it_cannot():
    get = lambda q: handler.lambda_handler({"requestContext": {"http": {"method": "GET"}}, "rawPath": "/places",
                                            "queryStringParameters": {"q": q}}, None)
    r = get("Lucknow")
    assert r["statusCode"] == 200 and json.loads(r["body"])["state"] == "UP"
    assert get("Atlantis")["statusCode"] == 404


def test_ask_route_says_what_it_used(monkeypatch):
    monkeypatch.setattr(qa, "answer_full", lambda q, user, lang: {"text": "₹78,000.", "used": [{"en": "the scheme list for Delhi", "hi": "दिल्ली की योजना सूची"}]})
    r = handler.lambda_handler({"requestContext": {"http": {"method": "POST"}}, "rawPath": "/ask",
                                "body": json.dumps({"question": "subsidy?", "lang": "en"})}, None)
    data = json.loads(r["body"])
    assert data["answer"] == "₹78,000." and data["used"][0]["en"] == "the scheme list for Delhi"
