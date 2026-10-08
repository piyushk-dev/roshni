"""After installation: is the system making what it should? And which reader does a photo need?

The household sends a photo of the inverter screen or the solar app. We compare its units with
what the panels should make this month at their location (the same conservative sunlight the
estimate used), and say what to do: nothing, clean, check, or keep it as warranty evidence.
"""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone

import boto3

from . import bill_reader
from .solar import SolarYield

IST = timezone(timedelta(hours=5, minutes=30))
SMOG_MONTHS = {11, 12, 1}

CLASSIFY = {"toolSpec": {"name": "classify", "description": "Say what this document is.", "inputSchema": {"json": {
    "type": "object",
    "properties": {"kind": {"type": "string", "enum": ["electricity_bill", "solar_quote", "inverter_reading", "other"],
                            "description": "inverter_reading: an inverter display or solar monitoring app showing units generated"}},
    "required": ["kind"]}}}}

READ = {"toolSpec": {"name": "record_generation", "description": "Record the generation shown.", "inputSchema": {"json": {
    "type": "object",
    "properties": {
        "kwh_today": {"type": "number"}, "kwh_this_month": {"type": "number"}, "kwh_total": {"type": "number"},
        "system_kw": {"type": "number", "description": "system capacity, if shown"},
        "date": {"type": "string", "description": "date shown on the screen, as printed"},
    }}}}}

TEXT = {
    "en": {
        "head": "☀️ Output check · {kw:g} kW system",
        "month": "This month so far: {actual:,.0f} units. Expected by today: about {expected:,.0f}.",
        "today": "Today: {actual:,.1f} units. A clear day here should give about {expected:,.1f}.",
        "ok": "✅ On track ({pct}% of expected). Nothing to do.",
        "low": "🧽 A little low ({pct}% of expected). Clean the panels with plain water early in the morning; Delhi dust alone costs about 10% a month.",
        "bad": "⚠️ Well below expected ({pct}%). Check the inverter for an error light or a tripped switch, and look for new shade. If it stays low, ask your vendor under warranty and keep these screenshots as evidence.",
        "smog": "Winter smog also cuts output by 6–12% in north India, so a slightly low number now is normal.",
        "assumed": "Using {kw:g} kW from your estimate. Reply SYSTEM 3.3 (your real size) to correct it.",
        "unread": "I couldn't read the units on that screen. Send a photo where the day's or month's kWh is clearly visible.",
    },
    "hi": {
        "head": "☀️ बिजली उत्पादन जाँच · {kw:g} kW सिस्टम",
        "month": "इस महीने अब तक: {actual:,.0f} यूनिट। आज तक लगभग {expected:,.0f} यूनिट होनी चाहिए थीं।",
        "today": "आज: {actual:,.1f} यूनिट। यहाँ साफ़ धूप वाले दिन लगभग {expected:,.1f} यूनिट बननी चाहिए।",
        "ok": "✅ सब ठीक ({pct}% अनुमान के मुकाबले)। कुछ करने की ज़रूरत नहीं।",
        "low": "🧽 थोड़ा कम ({pct}%)। सुबह-सुबह सादे पानी से पैनल साफ़ करें; दिल्ली की धूल से ही हर महीने लगभग 10% बिजली कम बनती है।",
        "bad": "⚠️ अनुमान से काफ़ी कम ({pct}%)। इन्वर्टर पर एरर लाइट या ट्रिप हुआ स्विच देखें, और नई छाया तो नहीं। कम बना रहे तो वारंटी के तहत वेंडर से कहें और ये स्क्रीनशॉट सबूत के तौर पर रखें।",
        "smog": "सर्दियों का स्मॉग उत्तर भारत में उत्पादन 6–12% घटा देता है, इसलिए अभी थोड़ा कम होना सामान्य है।",
        "assumed": "आपके अनुमान वाले {kw:g} kW मानकर। असली साइज़ बताने के लिए SYSTEM 3.3 लिखें।",
        "unread": "उस स्क्रीन पर यूनिट पढ़ी नहीं जा सकीं। ऐसी फोटो भेजें जिसमें दिन या महीने की kWh साफ़ दिखे।",
    },
}


def _client(client=None):
    return client or boto3.client("bedrock-runtime", region_name=bill_reader.REGION)


def classify(data: bytes, media_type: str, client=None) -> str:
    try:
        fields, _ = bill_reader.call_first_enabled(_client(client), bill_reader.tool_request(
            data, media_type, "What is this document? Call classify.", CLASSIFY, max_tokens=100))
        return fields.get("kind", "other")
    except Exception:
        return "electricity_bill"  # when unsure, the bill reader's own checks decide


def read_generation(data: bytes, media_type: str, client=None) -> dict:
    fields, _ = bill_reader.call_first_enabled(_client(client), bill_reader.tool_request(
        data, media_type, "This is a solar inverter display or monitoring app. Call record_generation with the "
        "kWh it shows for today, this month and in total. Copy numbers exactly; leave out what isn't shown.", READ, max_tokens=300))
    return fields


def check(reading: dict, kw: float, sy: SolarYield, now: datetime | None = None) -> dict | None:
    now = now or datetime.now(IST)
    month_yield = sy.monthly[now.month - 1] * kw
    days = calendar.monthrange(now.year, now.month)[1]
    if reading.get("kwh_this_month"):
        actual, expected, kind = reading["kwh_this_month"], month_yield * now.day / days, "month"
    elif reading.get("kwh_today"):
        actual, expected, kind = reading["kwh_today"], month_yield / days, "today"
    else:
        return None
    ratio = actual / expected if expected else 0
    verdict = "ok" if ratio >= 0.9 else "low" if ratio >= 0.75 else "bad"
    return {"kind": kind, "actual": actual, "expected": expected, "pct": round(ratio * 100), "verdict": verdict,
            "smog": now.month in SMOG_MONTHS and verdict != "ok"}


def message(result: dict | None, kw: float, lang: str, assumed: bool) -> str:
    t = TEXT[lang if lang in TEXT else "en"]
    if not result:
        return t["unread"]
    lines = [t["head"].format(kw=kw), t[result["kind"]].format(actual=result["actual"], expected=result["expected"]),
             t[result["verdict"]].format(pct=result["pct"])]
    if result["smog"]:
        lines.append(t["smog"])
    if assumed:
        lines.append(t["assumed"].format(kw=kw))
    return "\n".join(lines)
