"""Reads an electricity bill photo or PDF with a Bedrock vision model.

Only what the calculator needs is extracted. Name, address, phone and consumer number are
never asked for, so they never leave the model call.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

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

PROMPT = """This is an Indian household electricity bill. Call record_bill with what it shows.
Rules:
- Read numbers exactly as printed. If a field is not on the bill, leave it out. Never guess.
- monthly_history: every month in the bill's usage history table or graph, plus the current
  billing month. Use units actually billed (kWh), not amounts in rupees.
- amount_rs is the current month's charges, excluding arrears, late fees and previous dues.
- Do not record the consumer's name, address, phone number or account/consumer number."""

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
                "billing_month": {"type": "string", "description": "YYYY-MM"},
                "units_billed": {"type": "number"},
                "amount_rs": {"type": "number"},
                "monthly_history": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"month": {"type": "string", "description": "YYYY-MM"}, "units": {"type": "number"}},
                        "required": ["month", "units"],
                    },
                },
                "pincode": {"type": "string"},
            },
            "required": ["is_electricity_bill"],
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
    billing_month: str | None = None
    units_billed: float | None = None
    amount_rs: float | None = None
    monthly_units: dict[int, float] = field(default_factory=dict)  # calendar month -> units, latest year wins
    pincode: str | None = None
    model_id: str | None = None


def _content(data: bytes, media_type: str) -> dict:
    if media_type == "application/pdf":
        return {"document": {"format": "pdf", "name": "bill", "source": {"bytes": data}}}
    if media_type not in IMAGE_FORMATS:
        raise ValueError(f"unsupported file type {media_type}")
    return {"image": {"format": IMAGE_FORMATS[media_type], "source": {"bytes": data}}}


def _monthly_units(history: list[dict]) -> dict[int, float]:
    latest: dict[int, tuple[str, float]] = {}
    for row in history:
        month = str(row.get("month", ""))
        try:
            m = int(month[5:7])
        except ValueError:
            continue
        if 1 <= m <= 12 and (m not in latest or month > latest[m][0]):
            latest[m] = (month, float(row["units"]))
    return {m: units for m, (_, units) in sorted(latest.items())}


def read_bill(data: bytes, media_type: str, client=None) -> BillReading:
    client = client or boto3.client("bedrock-runtime", region_name=REGION)
    request = {
        "messages": [{"role": "user", "content": [_content(data, media_type), {"text": PROMPT}]}],
        "toolConfig": {"tools": [TOOL], "toolChoice": {"tool": {"name": "record_bill"}}},
        "inferenceConfig": {"maxTokens": 1500, "temperature": 0},
    }
    for i, model in enumerate(MODELS):
        try:
            response = client.converse(modelId=model, **request)
            break
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDeniedException" or i == len(MODELS) - 1:
                raise

    fields = next(c["toolUse"]["input"] for c in response["output"]["message"]["content"] if "toolUse" in c)
    history = fields.pop("monthly_history", [])
    reading = BillReading(**{k: v for k, v in fields.items() if k in BillReading.__dataclass_fields__}, model_id=model)
    reading.monthly_units = _monthly_units(history)
    if reading.billing_month and reading.units_billed is not None:
        reading.monthly_units.setdefault(int(reading.billing_month[5:7]), float(reading.units_billed))
    return reading
