"""Bill doctor: money a household can save from its bill alone, solar or not.

Each check reads only what the bill prints. Findings carry a yearly saving when one can be
worked out, and always a next step the household can take themselves.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from .format import inr
from .tariff import Tariff

LOAD_HEADROOM = 1.25  # keep a quarter above the highest demand seen, so a hot evening doesn't trip a penalty
EXPORT_EXPECTED = 30  # units a month; a net-metered home showing less than this probably isn't being credited


@dataclass
class Finding:
    code: str
    level: str  # "save" (money on the table), "check" (ask the provider), "ok"
    values: dict
    saves_rs: float = 0.0


TEXT = {
    "en": {
        "head": "🩺 Bill check-up",
        "total": "Worth about {total} a year, before any solar.",
        "load": "Your sanctioned load is {load:g} kW, but your highest demand was {peak:g} kW. Ask your provider to lower it to {new:g} kW: fixed charges drop by about {saves} a year. Any solar you add still fits under {new:g} kW.",
        "estimated": "This bill uses an estimated meter reading, not an actual one. Ask for an actual reading before paying; estimated bills are the most common billing dispute.",
        "other": "There's {amount} of \"other charges\" on this bill. Ask your provider in writing what it is for and for the order behind it.",
        "export_missing": "This is a net-metered bill but it shows almost no units sent to the grid. If your panels are working, ask for a meter check: the ministry flagged billing errors like this in July 2026.",
        "none": "Nothing to fix on this bill. Your load and charges look right.",
    },
    "hi": {
        "head": "🩺 बिल की जाँच",
        "total": "सोलर से पहले ही, सालाना लगभग {total} की बचत।",
        "load": "आपका स्वीकृत लोड {load:g} kW है, जबकि सबसे ज़्यादा माँग {peak:g} kW रही। बिजली कंपनी से इसे {new:g} kW करवाएँ: फ़िक्स्ड चार्ज सालाना लगभग {saves} कम होगा। सोलर लगवाएँ तो भी {new:g} kW में आ जाएगा।",
        "estimated": "यह बिल अनुमानित मीटर रीडिंग पर है, असली पर नहीं। भरने से पहले असली रीडिंग माँगें; अनुमानित बिल सबसे आम बिलिंग विवाद हैं।",
        "other": "इस बिल में {amount} के \"अन्य शुल्क\" हैं। बिजली कंपनी से लिखित में पूछें कि यह किसलिए है और किस आदेश के तहत।",
        "export_missing": "यह नेट-मीटर वाला बिल है, पर इसमें ग्रिड को भेजी यूनिट लगभग शून्य हैं। पैनल चल रहे हैं तो मीटर की जाँच माँगें: मंत्रालय ने जुलाई 2026 में ऐसी बिलिंग गड़बड़ियों पर ध्यान दिलाया था।",
        "none": "इस बिल में ठीक करने को कुछ नहीं। लोड और चार्ज सही लग रहे हैं।",
    },
}


def check(reading, tariff: Tariff) -> list[Finding]:
    found: list[Finding] = []
    load, peak = reading.sanctioned_load_kw, reading.max_demand_kw
    if load and peak and peak > 0:
        new = max(1, math.ceil(peak * LOAD_HEADROOM))
        if load - new >= 1:
            # fixed charges and the surcharges levied on them, a year of them
            saves = (tariff.bill(0, load).gross - tariff.bill(0, new).gross) * 12
            if saves > 500:
                found.append(Finding("load", "save", {"load": load, "peak": peak, "new": new, "saves": inr(round(saves, -2))}, saves))
    if reading.reading_type == "estimated":
        found.append(Finding("estimated", "check", {}))
    if reading.other_charges_rs and reading.other_charges_rs >= 100:
        found.append(Finding("other", "check", {"amount": inr(reading.other_charges_rs)}))
    if reading.net_metered and (reading.export_units or 0) < EXPORT_EXPECTED:
        found.append(Finding("export_missing", "check", {}))
    return found


def render(findings: list[Finding], lang: str = "en") -> dict:
    t = TEXT[lang if lang in TEXT else "en"]
    total = sum(f.saves_rs for f in findings)
    return {
        "head": t["head"],
        "total": t["total"].format(total=inr(round(total, -2))) if total else None,
        "items": [{"code": f.code, "level": f.level, "text": t[f.code].format(**f.values)} for f in findings],
        "none": t["none"] if not findings else None,
    }


def message(findings: list[Finding], lang: str = "en") -> str | None:
    if not findings:
        return None
    r = render(findings, lang)
    lines = [r["head"]] + ([r["total"]] if r["total"] else []) + [f"• {i['text']}" for i in r["items"]]
    return "\n".join(lines)


def to_dict(findings: list[Finding]) -> list[dict]:
    return [asdict(f) for f in findings]
