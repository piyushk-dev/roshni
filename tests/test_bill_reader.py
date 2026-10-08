import base64
import json

import pytest
from botocore.exceptions import ClientError
from conftest import HEAVY_AC

from surya import bill_reader, handler

FIELDS = {
    "is_electricity_bill": True,
    "discom": "BRPL",
    "discom_name": "BSES Rajdhani Power Limited",
    "sanctioned_load_kw": 5,
    "billing_month": "2026-09",
    "units_billed": 560,
    "amount_rs": 4512,
    "monthly_history": [{"month": f"2025-{m:02d}", "units": 1} for m in range(1, 9)]
    + [{"month": f"2026-{m:02d}", "units": u} for m, u in enumerate(HEAVY_AC[:8], start=1)]
    + [{"month": "2025-10", "units": 470}, {"month": "2025-11", "units": 390}, {"month": "2025-12", "units": 400}],
}


class FakeBedrock:
    def __init__(self, denied=()):
        self.denied, self.calls = set(denied), []

    def converse(self, modelId, **request):
        self.calls.append(modelId)
        if modelId in self.denied:
            raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "no"}}, "Converse")
        return {"output": {"message": {"content": [{"toolUse": {"input": json.loads(json.dumps(FIELDS))}}]}}}


def test_latest_year_wins_and_current_month_is_added():
    r = bill_reader.read_bill(b"img", "image/png", client=FakeBedrock())
    assert r.monthly_units[1] == HEAVY_AC[0]  # 2026 beats the 2025 placeholder
    assert r.monthly_units[10] == 470
    assert r.monthly_units[9] == 560  # from units_billed, the history stops at August
    assert len(r.monthly_units) == 12


def test_falls_back_when_a_model_is_not_enabled():
    fake = FakeBedrock(denied={bill_reader.MODELS[0]})
    r = bill_reader.read_bill(b"img", "image/png", client=fake)
    assert fake.calls == bill_reader.MODELS[:2]
    assert r.model_id == bill_reader.MODELS[1]


def test_rejects_unknown_file_types():
    with pytest.raises(ValueError):
        bill_reader.read_bill(b"x", "text/plain", client=FakeBedrock())


def test_bill_route(monkeypatch, delhi_yield):
    monkeypatch.setattr(handler, "_yield_for", lambda lat, lon: delhi_yield)
    real = bill_reader.read_bill
    monkeypatch.setattr(bill_reader, "read_bill", lambda data, mt: real(data, mt, client=FakeBedrock()))
    event = {
        "requestContext": {"http": {"method": "POST"}},
        "rawPath": "/bill",
        "body": json.dumps({"file_base64": base64.b64encode(b"img").decode(), "media_type": "image/png"}),
    }
    out = handler.lambda_handler(event, None)
    assert out["statusCode"] == 200
    body = json.loads(out["body"])
    assert body["bill"]["discom"] == "BRPL"
    assert body["analysis"]["verdict"] == "go"
    assert "consumer" not in json.dumps(body["bill"]).lower()
