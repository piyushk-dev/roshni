"""Reads an electricity bill photo or PDF with a Bedrock vision model.

Only what the calculator needs is extracted. Name, address, phone and consumer number are
never asked for, so they never leave the model call.

The model only transcribes: each usage row's dates, days and units exactly as printed.
Working out which month a row belongs to happens here. On real, skewed bill photos models
read the units column reliably but scramble the history table's dates, so months are counted
back from the current billing period, in printed order; row dates only settle the order.
"""

from __future__ import annotations

import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from statistics import median
from datetime import date, datetime, timedelta

import boto3
from botocore.exceptions import ClientError

# Tried in order until one is enabled on the account; the `in.` profile keeps the bill inside India
MODELS = list(dict.fromkeys(m for m in (
    os.environ.get("BEDROCK_MODEL_ID"),
    "global.anthropic.claude-haiku-5-5",
    "in.anthropic.claude-haiku-4-5-20251001-v1:0",
    "global.amazon.nova-2-lite-v1:0",
) if m))
REGION = os.environ.get("BEDROCK_REGION", "ap-south-1")
IMAGE_FORMATS = {"image/jpeg": "jpeg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
DAYS_PER_MONTH = 30.44
READS = 3  # single readings of a phone photo drift; three in parallel cost one read's latency
ENERGY_RS_PER_UNIT = (1.5, 10.0)  # any Indian domestic slab average falls in here; outside it, the model misread
DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y", "%d-%b-%Y", "%d-%b-%y", "%d %b %Y", "%Y-%m-%d")

PROMPT = """This is an Indian household electricity bill. Call record_bill with what it shows.
Rules:
- sanctioned_load_kw: the "Sanctioned Load" (or connected load) in kW, as printed.
- Transcribe, don't interpret. Copy dates exactly as printed (Indian bills print DD-MM-YYYY).
  If a field is not on the bill, leave it out. Never guess or fill gaps.
- usage_rows: one entry per row of the consumption history table, plus the current billing
  period. Take units from the units (kWh) column. Do not put the number of days, a meter
  reading or a rupee amount in units.
- usage_rows must be in the same order as printed, and must not repeat the current period.
- energy_charge_rs: the total energy charge for this billing period (often labelled "Energy
  Charge" or "Slabwise Energy Charge", the sum of the slab amounts). Not the bill total.
- current_charges_rs: this billing period's total charges, before arrears, previous dues,
  late payment surcharge, subsidy or rebate.
- Do not record the consumer's name, address, phone number, email or account/consumer number."""

_ROW = {
    "type": "object",
    "properties": {
        "from_date": {"type": "string", "description": "start of the period, exactly as printed"},
        "to_date": {"type": "string", "description": "end of the period, exactly as printed"},
        "days": {"type": "number", "description": "number of days, if printed"},
        "units": {"type": "number", "description": "kWh consumed in the period"},
    },
    "required": ["units"],
}

TOOL = {
    "toolSpec": {
        "name": "record_bill",
        "description": "Record the fields read from the electricity bill.",
        "inputSchema": {"json": {
            "type": "object",
            "properties": {
                "is_electricity_bill": {"type": "boolean"},
                "discom": {"type": "string", "enum": ["BRPL", "BYPL", "TPDDL", "OTHER"],
                           "description": "BRPL = BSES Rajdhani, BYPL = BSES Yamuna, TPDDL = Tata Power-DDL"},
                "discom_name": {"type": "string", "description": "Provider name as printed"},
                "category": {"type": "string", "description": "Tariff category, e.g. Domestic"},
                "sanctioned_load_kw": {"type": "number"},
                "current_period": _ROW,
                "usage_rows": {"type": "array", "items": _ROW},
                "energy_charge_rs": {"type": "number"},
                "current_charges_rs": {"type": "number"},
                "bill_date": {"type": "string", "description": "date the bill was issued, exactly as printed"},
                "pincode": {"type": "string"},
            },
            "required": ["is_electricity_bill", "discom", "sanctioned_load_kw", "current_period", "usage_rows"],
        }},
    }
}


@dataclass
class BillReading:
    is_electricity_bill: bool
    discom: str | None = None
    discom_name: str | None = None
    category: str | None = None
    sanctioned_load_kw: float | None = None
    billing_month: str | None = None  # YYYY-MM of the current period
    units_billed: float | None = None  # current period, scaled to a standard month
    energy_charge_rs: float | None = None  # current period's energy charge, scaled to a standard month
    amount_rs: float | None = None  # current period's total charges as printed
    monthly_units: dict[int, float] = field(default_factory=dict)  # calendar month -> units
    pincode: str | None = None
    model_id: str | None = None


def _content(data: bytes, media_type: str) -> dict:
    if media_type == "application/pdf":
        return {"document": {"format": "pdf", "name": "bill", "source": {"bytes": data}}}
    if media_type not in IMAGE_FORMATS:
        raise ValueError(f"unsupported file type {media_type}")
    return {"image": {"format": IMAGE_FORMATS[media_type], "source": {"bytes": data}}}


def parse_date(text: str | None) -> date | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(text).strip(), fmt).date()
        except (TypeError, ValueError):
            continue
    return None


def _period(row: dict) -> tuple[date, float, float] | None:
    """(midpoint, units scaled to a standard month, days) for one usage row, or None if its dates don't parse."""
    start, end = parse_date(row.get("from_date")), parse_date(row.get("to_date"))
    if not start or not end or end <= start:
        return None
    days = (end - start).days + 1
    if row.get("days") and abs(row["days"] - days) <= 2:
        days = row["days"]
    if not 20 <= days <= 40:  # not a monthly bill period; skip rather than guess
        return None
    return start + (end - start) / 2, float(row["units"]) * DAYS_PER_MONTH / days, days


def _scaled(row: dict) -> float:
    days = row.get("days")
    return float(row["units"]) * DAYS_PER_MONTH / days if days and 20 <= days <= 40 else float(row["units"])


def _drop_days_column(rows: list[dict]) -> list[dict]:
    """Models sometimes read the "No. of Days" column as one more usage row at the end of the table."""
    while len(rows) > 2:
        last, others = rows[-1]["units"], sorted(r["units"] for r in rows[:-1])
        if 28 <= last <= 33 and last < 0.6 * others[len(others) // 2]:
            rows = rows[:-1]
        else:
            break
    return rows


def _newest_first(rows: list[dict]) -> bool:
    ends = [d for d in (parse_date(r.get("to_date")) or parse_date(r.get("from_date")) for r in rows) if d]
    return len(ends) < 2 or ends[0] >= ends[-1]  # Indian bills usually list the latest month first


def anchor(current: dict | None, bill_date: str | None = None) -> tuple[date, float, float | None] | None:
    """(a date inside the current billing period, its units scaled to a standard month, its days).

    Falls back from the full period to either end date, then to the bill's issue date, because
    models often misread one of the two period dates on a photo."""
    if not current or current.get("units") is None:
        return None
    p = _period(current)
    if p:
        return p
    days = current.get("days") if current.get("days") and 20 <= current["days"] <= 40 else None
    units = _scaled(current)
    half = timedelta(days=(days or DAYS_PER_MONTH) / 2)
    if end := parse_date(current.get("to_date")):
        return end - half, units, days
    if start := parse_date(current.get("from_date")):
        return start + half, units, days
    if issued := parse_date(bill_date):
        return issued - half - timedelta(days=5), units, days  # bills go out a few days after the period ends
    return None


def monthly_units(rows: list[dict], current: dict | None, bill_date: str | None = None) -> dict[int, float]:
    """Calendar month -> units. Months are counted back from the current period in printed order."""
    p = anchor(current, bill_date)
    if not p:  # no anchor: trust each row's own dates
        out: dict[int, tuple[date, float]] = {}
        for row in rows:
            q = _period(row)
            if q and (q[0].month not in out or q[0] > out[q[0].month][0]):
                out[q[0].month] = (q[0], round(q[1], 1))
        return {m: u for m, (_, u) in sorted(out.items())}

    key = lambda r: (r.get("units"), r.get("from_date"), r.get("to_date"))
    history = [r for r in rows if r.get("units") is not None and key(r) != key(current)]
    history = _drop_days_column(history)
    if not _newest_first(history):
        history = history[::-1]
    if history and history[0]["units"] == current["units"]:  # the current period repeated with misread dates
        history = history[1:]
    out = {p[0].month: round(p[1], 1)}
    for back, row in enumerate(history[:11], start=1):
        out.setdefault((p[0].month - 1 - back) % 12 + 1, round(_scaled(row), 1))
    return dict(sorted(out.items()))


def _reading(f: dict, model: str) -> BillReading:
    reading = BillReading(
        is_electricity_bill=bool(f.get("is_electricity_bill")),
        discom=f.get("discom"),
        discom_name=f.get("discom_name"),
        category=f.get("category"),
        sanctioned_load_kw=f.get("sanctioned_load_kw"),
        pincode=f.get("pincode"),
        model_id=model,
    )
    current = f.get("current_period") or None
    reading.monthly_units = monthly_units(f.get("usage_rows", []), current, f.get("bill_date"))
    reading.amount_rs = f.get("current_charges_rs")

    p = anchor(current, f.get("bill_date"))
    if p:
        mid, units, days = p
        reading.billing_month = f"{mid:%Y-%m}"
        reading.units_billed = round(units, 1)
        energy = f.get("energy_charge_rs")
        low, high = ENERGY_RS_PER_UNIT
        if energy and current.get("units") and low <= energy / current["units"] <= high:
            reading.energy_charge_rs = round(energy * DAYS_PER_MONTH / (days or DAYS_PER_MONTH), 2)
    return reading


def _majority(values: list):
    values = [v for v in values if v is not None]
    return Counter(values).most_common(1)[0][0] if values else None


def consensus(readings: list[BillReading]) -> BillReading:
    """What most readings agree on: majority load, provider and month; per-month median units,
    keeping only months that at least half the readings saw. One stray or dropped row can't move it."""
    bills = [r for r in readings if r.is_electricity_bill]
    if len(bills) * 2 < len(readings):
        return next(r for r in readings if not r.is_electricity_bill)
    best = max(bills, key=lambda r: (bool(r.sanctioned_load_kw), bool(r.billing_month), len(r.monthly_units)))
    best.discom = _majority([r.discom for r in bills]) or best.discom
    best.sanctioned_load_kw = _majority([r.sanctioned_load_kw for r in bills])
    best.billing_month = _majority([r.billing_month for r in bills])

    seen = [r for r in bills if r.monthly_units]
    need = (len(seen) + 1) // 2
    months = {}
    for m in range(1, 13):
        values = [r.monthly_units[m] for r in seen if m in r.monthly_units]
        if values and len(values) >= need:
            months[m] = median(values)
    best.monthly_units = months
    same_period = [r for r in bills if r.billing_month == best.billing_month]
    units = [r.units_billed for r in same_period if r.units_billed is not None]
    energy = [r.energy_charge_rs for r in same_period if r.energy_charge_rs is not None]
    best.units_billed = median(units) if units else None
    best.energy_charge_rs = median(energy) if energy else None
    return best


def tool_request(data: bytes, media_type: str, prompt: str, tool: dict, max_tokens: int = 2000) -> dict:
    """A Converse request that shows the document and forces one call to `tool`."""
    return {
        "messages": [{"role": "user", "content": [_content(data, media_type), {"text": prompt}]}],
        "toolConfig": {"tools": [tool], "toolChoice": {"tool": {"name": tool["toolSpec"]["name"]}}},
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0},
    }


def call_tool(client, model: str, request: dict) -> dict:
    response = client.converse(modelId=model, **request)
    return next(c["toolUse"]["input"] for c in response["output"]["message"]["content"] if "toolUse" in c)


def call_first_enabled(client, request: dict) -> tuple[dict, str]:
    """(tool input, model id) from the first model in MODELS this account may use."""
    for i, model in enumerate(MODELS):
        try:
            return call_tool(client, model, request), model
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDeniedException" or i == len(MODELS) - 1:
                raise
    raise RuntimeError("no Bedrock model configured")


def read_bill(data: bytes, media_type: str, client=None, reads: int = READS) -> BillReading:
    """`reads` independent readings in parallel, reduced to what they agree on."""
    client = client or boto3.client("bedrock-runtime", region_name=REGION)
    request = tool_request(data, media_type, PROMPT, TOOL)

    def one(_) -> BillReading:
        fields, model = call_first_enabled(client, request)
        return _reading(fields, model)

    with ThreadPoolExecutor(reads) as pool:
        return consensus(list(pool.map(one, range(reads))))
