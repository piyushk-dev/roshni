import json

from conftest import HEAVY_AC, LOW, months

from surya import handler, pipeline
from surya.calculator import Household, analyze
from surya.format import inr, message


def test_indian_digit_grouping():
    assert inr(0) == "₹0"
    assert inr(999) == "₹999"
    assert inr(195000) == "₹1,95,000"
    assert inr(12345678) == "₹1,23,45,678"
    assert inr(-10579) == "-₹10,579"


def test_messages_render_in_both_languages(delhi_yield):
    go = analyze(Household("BRPL", 5, months(HEAVY_AC)), delhi_yield)
    skip = analyze(Household("BYPL", 2, months(LOW)), delhi_yield)
    assert "Best size" in message(go, "en")
    assert "सही साइज़" in message(go, "hi")
    assert "isn't worth it" in message(skip, "en")
    assert "{" not in message(go, "hi") + message(skip, "hi")


def _event(method, path, body=None):
    return {"requestContext": {"http": {"method": method}}, "rawPath": path, "body": json.dumps(body) if body else None}


def test_handler_routes(monkeypatch, delhi_yield):
    monkeypatch.setattr(pipeline, "yield_for", lambda lat, lon: delhi_yield)
    assert handler.lambda_handler(_event("GET", "/health"), None)["statusCode"] == 200
    assert handler.lambda_handler(_event("GET", "/nope"), None)["statusCode"] == 404

    ok = handler.lambda_handler(_event("POST", "/analyze", {
        "discom": "BRPL", "sanctioned_kw": 5, "monthly_units": {str(m): u for m, u in months(HEAVY_AC).items()}, "lang": "hi",
    }), None)
    assert ok["statusCode"] == 200
    body = json.loads(ok["body"])
    assert body["analysis"]["verdict"] == "go"
    assert "सोलर" in body["message"]

    bad = handler.lambda_handler(_event("POST", "/analyze", {"discom": "NOPE", "sanctioned_kw": 3, "monthly_units": {"1": 100}}), None)
    assert bad["statusCode"] == 400
