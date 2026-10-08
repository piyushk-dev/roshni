import base64
import json

import pytest
from botocore.exceptions import ClientError
from surya import bill_reader, handler, pipeline

CURRENT = {"from_date": "09-06-2026", "to_date": "06-07-2026", "units": 562}
# What Nova 2 Lite returned for a real BRPL bill photo: every unit right, newest first, dates scrambled,
# and the current period repeated at the top
REAL_ROWS = [
    {"from_date": "09-06-2026", "to_date": "06-07-2026", "units": 562},
    {"from_date": "09-05-2026", "to_date": "06-06-2026", "units": 560},
    {"from_date": "08-05-2026", "to_date": "06-04-2026", "units": 178},
    {"from_date": "08-04-2026", "to_date": "06-03-2026", "units": 155},
    {"from_date": "09-03-2026", "to_date": "06-02-2026", "units": 85},
    {"from_date": "11-02-2026", "to_date": "06-01-2026", "units": 78},
    {"from_date": "06-01-2026", "to_date": "05-01-2026", "units": 68},
]
FIELDS = {
    "is_electricity_bill": True,
    "discom": "BRPL",
    "discom_name": "BSES Rajdhani Power Limited",
    "sanctioned_load_kw": 6,
    "current_period": CURRENT,
    "usage_rows": REAL_ROWS,
    "energy_charge_rs": 2634.00,
    "current_charges_rs": 9194.58,
}


class FakeBedrock:
    def __init__(self, denied=()):
        self.denied, self.calls, self.fields = set(denied), [], FIELDS

    def converse(self, modelId, **request):
        self.calls.append(modelId)
        if modelId in self.denied:
            raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "no"}}, "Converse")
        return {"output": {"message": {"content": [{"toolUse": {"input": json.loads(json.dumps(self.fields))}}]}}}


def test_real_bill_months_are_counted_back_from_the_current_period():
    r = bill_reader.read_bill(b"img", "image/png", client=FakeBedrock())
    # 562 units over 28 days is 611 in a standard month; the duplicate current row is dropped
    assert r.monthly_units == {6: 611.0, 5: 560.0, 4: 178.0, 3: 155.0, 2: 85.0, 1: 78.0, 12: 68.0}
    assert r.billing_month == "2026-06"
    assert r.energy_charge_rs == pytest.approx(2634.00 * 30.44 / 28, abs=0.01)
    assert r.amount_rs == 9194.58


def test_oldest_first_tables_are_reversed():
    rows = [{"from_date": f"01-{m:02d}-2026", "to_date": f"28-{m:02d}-2026", "units": m * 10} for m in (3, 4, 5)]
    out = bill_reader.monthly_units(rows, {"from_date": "01-06-2026", "to_date": "30-06-2026", "units": 600})
    assert out == {3: 30.0, 4: 40.0, 5: 50.0, 6: 608.8}


def test_without_a_current_period_each_row_uses_its_own_dates():
    rows = [{"from_date": "09-05-2026", "to_date": "08-06-2026", "days": 31, "units": 560}]
    assert bill_reader.monthly_units(rows, None) == {5: round(560 * 30.44 / 31, 1)}


def test_days_column_misread_as_a_row_is_dropped():
    rows = [{"units": u} for u in (560, 178, 155, 85, 78, 68, 31)]
    out = bill_reader.monthly_units(rows, CURRENT)
    assert 11 not in out and out[12] == 68.0


def test_bill_total_misread_as_energy_charge_is_ignored():
    fake = FakeBedrock()
    fake.fields = {**FIELDS, "energy_charge_rs": 9194.58}
    assert bill_reader.read_bill(b"img", "image/png", client=fake).energy_charge_rs is None


def _reading(**changes):
    return bill_reader._reading({**FIELDS, **changes}, "m")


def test_consensus_drops_a_stray_month_and_restores_a_dropped_one():
    good = _reading()
    stray = _reading(usage_rows=REAL_ROWS + [{"units": 62}])   # one reading invents November
    dropped = _reading(usage_rows=[r for r in REAL_ROWS if r["units"] != 560])  # one misses May
    r = bill_reader.consensus([good, stray, dropped])
    assert r.monthly_units == good.monthly_units
    assert 11 not in r.monthly_units and r.monthly_units[5] == 560.0


def test_consensus_takes_the_majority_load():
    r = bill_reader.consensus([_reading(), _reading(sanctioned_load_kw=None), _reading(sanctioned_load_kw=60)])
    assert r.sanctioned_load_kw in (6, 60) and bill_reader.consensus([_reading(), _reading(), _reading(sanctioned_load_kw=60)]).sanctioned_load_kw == 6


def test_majority_not_a_bill_wins():
    no = bill_reader._reading({"is_electricity_bill": False}, "m")
    assert not bill_reader.consensus([no, no, _reading()]).is_electricity_bill


def test_three_reads_in_parallel():
    fake = FakeBedrock()
    bill_reader.read_bill(b"img", "image/png", client=fake)
    assert len(fake.calls) == bill_reader.READS


def test_misread_current_period_still_anchors_the_months():
    """Seen on the real bill under load: the period came back as 06-07 to 08-07, with 28 days printed."""
    bad = {"from_date": "06-07-2026", "to_date": "08-07-2026", "days": 28, "units": 562}
    out = bill_reader.monthly_units(REAL_ROWS, bad)
    assert out == {6: 611.0, 5: 560.0, 4: 178.0, 3: 155.0, 2: 85.0, 1: 78.0, 12: 68.0}


def test_bill_date_is_the_last_resort_anchor():
    out = bill_reader.monthly_units([{"units": 300}], {"units": 400}, bill_date="11-07-2026")
    assert out == {6: 400.0, 5: 300.0}


def test_indian_dates_are_day_first():
    assert bill_reader.parse_date("09-05-2026").month == 5
    assert bill_reader.parse_date("06-JUL-26").month == 7
    assert bill_reader.parse_date("not a date") is None


def test_falls_back_when_a_model_is_not_enabled():
    fake = FakeBedrock(denied={bill_reader.MODELS[0]})
    r = bill_reader.read_bill(b"img", "image/png", client=fake)
    assert bill_reader.MODELS[0] in fake.calls
    assert r.model_id == bill_reader.MODELS[1]


def test_rejects_unknown_file_types():
    with pytest.raises(ValueError):
        bill_reader.read_bill(b"x", "text/plain", client=FakeBedrock())


def test_bill_route(monkeypatch, delhi_yield):
    monkeypatch.setattr(pipeline, "yield_for", lambda lat, lon: delhi_yield)
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
    assert body["analysis"]["calibration"] == pytest.approx(1.0, abs=0.02)  # the energy-charge model matches the bill
    assert "consumer" not in json.dumps(body["bill"]).lower()
