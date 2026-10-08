"""Checks a rooftop-solar vendor's quotation before the household signs.

The model only transcribes the quote. Every judgement below is a plain rule against the
PM Surya Ghar scheme and market prices, so the same quote always gets the same answer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import boto3

from . import bill_reader
from .format import inr
from .scheme import SCHEME, central_subsidy

GST_ON_SYSTEMS = 0.089  # 70% goods at 5% + 30% installation services at 18%
STATED = {"type": "string", "enum": ["yes", "no", "not_stated"]}

PROMPT = """This is a quotation from a rooftop solar vendor in India. Call record_quote with what it shows.
Rules:
- Transcribe, don't judge. Use "not_stated" when the quote doesn't mention something. Never guess.
- dcr is "yes" only if the quote explicitly says DCR, domestic content requirement or made with
  Indian cells; "no" if it says non-DCR, DCR-exempt or imported cells.
- total_price_rs is the full price of the system before any subsidy is deducted.
- gst_included is "no" when the price says "+ GST", "GST extra" or "excluding GST"; "yes" when it
  says "including GST" or "inclusive of taxes".
- net_meter_included is "no" when net metering is charged extra or paid by the customer.
- warranty years: numbers only, as printed.
- Do not record the customer's name, address or phone number."""

TOOL = {
    "toolSpec": {
        "name": "record_quote",
        "description": "Record the fields read from the solar quotation.",
        "inputSchema": {"json": {
            "type": "object",
            "properties": {
                "is_solar_quote": {"type": "boolean"},
                "vendor_name": {"type": "string"},
                "system_kw": {"type": "number"},
                "total_price_rs": {"type": "number"},
                "gst_included": STATED,
                "subsidy_promised_rs": {"type": "number", "description": "subsidy amount the vendor mentions"},
                "module_brand": {"type": "string"},
                "module_watt": {"type": "number"},
                "module_count": {"type": "number"},
                "dcr": STATED,
                "inverter_brand": {"type": "string"},
                "inverter_kw": {"type": "number"},
                "module_performance_warranty_years": {"type": "number"},
                "inverter_warranty_years": {"type": "number"},
                "system_warranty_years": {"type": "number", "description": "workmanship or comprehensive maintenance"},
                "net_meter_included": STATED,
                "structure_included": STATED,
                "earthing_included": STATED,
                "advance_pct": {"type": "number"},
                "state": {"type": "string", "description": "two-letter Indian state code of the installation, if shown"},
            },
            "required": ["is_solar_quote", "dcr"],
        }},
    }
}

TEXT = {
    "en": {
        "head": "🧾 Quote check: {vendor} · {kw:g} kW · {total}",
        "red": "🔴 Don't sign yet. Fix these first:",
        "amber": "🟠 Negotiate before you sign:",
        "ok": "✅ This quote looks fair.",
        "ask": "Ask the vendor:",
        "foot": "Prices are compared with {low}–{high} per kW including GST: {basis}.",
        "basis_live": "the middle half of {n} recent quotes in {state}",
        "basis_seed": "typical 2026 market rates, until enough local quotes come in",
        "not_dcr": "These panels are not DCR (made with Indian cells). Under PM Surya Ghar that means no subsidy: you'd lose {subsidy}.",
        "dcr_unstated": "The quote doesn't say the panels are DCR. Without DCR panels the {subsidy} subsidy is rejected at inspection. Ask for \"DCR\" in writing, plus the DCR certificate.",
        "subsidy_overpromised": "The quote promises {promised} in subsidy, but the scheme maximum for {kw:g} kW is {max}.",
        "price_high": "{per_kw} per kW is above the typical {low}–{high}. That's about {extra} more than a fair quote. Get a second quote.",
        "price_low": "{per_kw} per kW is unusually cheap. Check the panel brand, its ALMM listing and the warranties.",
        "capacity_mismatch": "{count:g} × {watt:g} W panels make {dc:g} kW, but the quote says {kw:g} kW. Ask what you'll actually get.",
        "inverter_small": "A {inv:g} kW inverter is small for a {kw:g} kW system.",
        "short_module_warranty": "Panel performance warranty is only {years_text}; 25 years is standard.",
        "short_inverter_warranty": "Inverter warranty is only {years_text}; ask for at least 5 years.",
        "short_system_warranty": "System warranty or maintenance is only {years_text}; ask for at least 5 years.",
        "big_advance": "{pct:g}% advance is a lot. Tie payments to installation milestones.",
        "gst_excluded": "GST is extra. This comparison uses an illustrative 8.9% EPC blend; confirm the applicable tax and final GST-inclusive invoice with your installer.",
        "net_meter": "Who pays for the net meter and the electricity provider's fees?",
        "structure": "Is the mounting structure (rust-proof GI) included?",
        "earthing": "Are earthing and a lightning arrester included?",
        "not_quote": "That doesn't look like a solar quotation. Send a photo or PDF of the vendor's quote.",
    },
    "hi": {
        "head": "🧾 कोटेशन जाँच: {vendor} · {kw:g} kW · {total}",
        "red": "🔴 अभी साइन न करें। पहले ये ठीक करवाएँ:",
        "amber": "🟠 साइन करने से पहले मोलभाव करें:",
        "ok": "✅ यह कोटेशन ठीक लग रहा है।",
        "ask": "वेंडर से पूछें:",
        "foot": "कीमतों की तुलना {low}–{high} प्रति kW (GST सहित) से की गई है: {basis}।",
        "basis_live": "{state} के {n} हाल के कोटेशन का बीच का हिस्सा",
        "basis_seed": "2026 के आम बाज़ार रेट, जब तक पर्याप्त स्थानीय कोटेशन नहीं आते",
        "not_dcr": "ये पैनल DCR (भारत में बने सेल) नहीं हैं। PM सूर्य घर में इसका मतलब है कोई सब्सिडी नहीं: आपके {subsidy} चले जाएँगे।",
        "dcr_unstated": "कोटेशन में पैनल के DCR होने की बात नहीं लिखी। DCR पैनल के बिना जाँच में {subsidy} की सब्सिडी खारिज हो जाती है। लिखित में \"DCR\" और DCR सर्टिफ़िकेट माँगें।",
        "subsidy_overpromised": "कोटेशन में {promised} सब्सिडी का वादा है, लेकिन {kw:g} kW के लिए योजना में अधिकतम {max} ही है।",
        "price_high": "{per_kw} प्रति kW आम रेट ({low}–{high}) से ज़्यादा है। सही कोटेशन से लगभग {extra} ज़्यादा लग रहे हैं। दूसरा कोटेशन लें।",
        "price_low": "{per_kw} प्रति kW बहुत सस्ता है। पैनल का ब्रांड, ALMM लिस्टिंग और वारंटी ज़रूर जाँचें।",
        "capacity_mismatch": "{count:g} × {watt:g}W पैनल = {dc:g} kW, लेकिन कोटेशन {kw:g} kW का है। पूछें कि असल में कितने kW लगेंगे।",
        "inverter_small": "{inv:g} kW का इन्वर्टर {kw:g} kW सिस्टम के लिए छोटा है।",
        "short_module_warranty": "पैनल की परफ़ॉर्मेंस वारंटी सिर्फ़ {years:g} साल है; आम तौर पर 25 साल होती है।",
        "short_inverter_warranty": "इन्वर्टर की वारंटी सिर्फ़ {years:g} साल है; कम से कम 5 साल माँगें।",
        "short_system_warranty": "पूरे सिस्टम की वारंटी या मेंटेनेंस सिर्फ़ {years:g} साल है; कम से कम 5 साल माँगें।",
        "big_advance": "{pct:g}% एडवांस बहुत ज़्यादा है। भुगतान काम के चरणों से जोड़ें।",
        "gst_excluded": "GST अलग है। तुलना में उदाहरण वाला 8.9% EPC मिश्रण है; लागू टैक्स और GST सहित आख़िरी बिल वेंडर से पुष्टि करें।",
        "net_meter": "नेट मीटर और बिजली कंपनी की फ़ीस कौन देगा?",
        "structure": "क्या माउंटिंग स्ट्रक्चर (जंग-रोधी GI) कीमत में शामिल है?",
        "earthing": "क्या अर्थिंग और लाइटनिंग अरेस्टर शामिल हैं?",
        "not_quote": "यह सोलर कोटेशन नहीं लग रहा। वेंडर के कोटेशन की फोटो या PDF भेजें।",
    },
}


@dataclass
class Flag:
    level: str  # "red", "amber", "ask" or "note"
    code: str
    values: dict


def check(q: dict, state: str = "DL", band: dict | None = None) -> list[Flag]:
    flags: list[Flag] = []
    count, watt = q.get("module_count"), q.get("module_watt")
    dc = round(count * watt / 1000, 2) if count and watt else None
    kw = q.get("system_kw") or dc
    max_subsidy = central_subsidy(kw, state) if kw else SCHEME["pmsgy"]["central_subsidy"]["general"]["cap"]

    if q.get("dcr") == "no":
        flags.append(Flag("red", "not_dcr", {"subsidy": inr(max_subsidy)}))
    elif q.get("dcr") != "yes":
        flags.append(Flag("red", "dcr_unstated", {"subsidy": inr(max_subsidy)}))
    promised = q.get("subsidy_promised_rs")
    if kw and promised and promised > max_subsidy + 1000:
        flags.append(Flag("red", "subsidy_overpromised", {"promised": inr(promised), "kw": kw, "max": inr(max_subsidy)}))

    total = q.get("total_price_rs")
    if kw and total:
        if q.get("gst_included") == "no":
            total *= 1 + GST_ON_SYSTEMS
            flags.append(Flag("note", "gst_excluded", {}))
        band = band or SCHEME["cost_rs_per_kw"]["upto_3kw" if kw <= 3 else "above_3kw"]
        per_kw = total / kw
        prices = {"per_kw": inr(per_kw), "low": inr(band["low"]), "high": inr(band["high"])}
        if per_kw > band["high"]:
            flags.append(Flag("amber", "price_high", {**prices, "extra": inr(round(total - kw * band["typical"], -3))}))
        elif per_kw < 0.85 * band["low"]:
            flags.append(Flag("amber", "price_low", prices))

    if dc and q.get("system_kw") and dc < 0.95 * q["system_kw"]:  # more panels than quoted is common and fine
        flags.append(Flag("amber", "capacity_mismatch", {"count": count, "watt": watt, "dc": dc, "kw": q["system_kw"]}))
    if kw and q.get("inverter_kw") and q["inverter_kw"] < 0.8 * kw:
        flags.append(Flag("amber", "inverter_small", {"inv": q["inverter_kw"], "kw": kw}))
    for field, code, minimum in (
        ("module_performance_warranty_years", "short_module_warranty", 25),
        ("inverter_warranty_years", "short_inverter_warranty", 5),
        ("system_warranty_years", "short_system_warranty", 5),
    ):
        if q.get(field) and q[field] < minimum:
            years = q[field]
            flags.append(Flag("amber", code, {"years": years, "years_text": f"{years:g} year" + ("" if years == 1 else "s")}))
    if q.get("advance_pct") and q["advance_pct"] > 30:
        flags.append(Flag("amber", "big_advance", {"pct": q["advance_pct"]}))

    for field, code in (("net_meter_included", "net_meter"), ("structure_included", "structure"), ("earthing_included", "earthing")):
        if q.get(field) != "yes":
            flags.append(Flag("ask", code, {}))
    return flags


def verdict(flags: list[Flag]) -> str:
    levels = {f.level for f in flags}
    return "red" if "red" in levels else "amber" if "amber" in levels else "ok"


def lines(flags: list[Flag], lang: str) -> dict[str, list[str]]:
    t = TEXT[lang if lang in TEXT else "en"]
    out: dict[str, list[str]] = {"red": [], "amber": [], "note": [], "ask": []}
    for f in flags:
        out[f.level].append(t[f.code].format(**f.values))
    return out


def render(q: dict, flags: list[Flag], lang: str = "en", band: dict | None = None) -> dict:
    """The check as ready-made sentences: verdict, headline, issues, notes, questions, footnote."""
    t = TEXT[lang if lang in TEXT else "en"]
    kw = q.get("system_kw") or 0
    band = band or SCHEME["cost_rs_per_kw"]["upto_3kw" if kw <= 3 else "above_3kw"]
    basis = t["basis_live"].format(n=band["quotes"], state=q.get("state") or "your state") if band.get("live") else t["basis_seed"]
    v = verdict(flags)
    return {
        "verdict": v,
        "title": t[v],
        "head": t["head"].format(vendor=q.get("vendor_name") or "vendor", kw=kw, total=inr(q["total_price_rs"]) if q.get("total_price_rs") else "—"),
        **lines(flags, lang),
        "ask_title": t["ask"],
        "foot": t["foot"].format(low=inr(band["low"]), high=inr(band["high"]), basis=basis),
    }


def message(q: dict, flags: list[Flag], lang: str = "en", band: dict | None = None) -> str:
    if not q.get("is_solar_quote"):
        return TEXT[lang if lang in TEXT else "en"]["not_quote"]
    r = render(q, flags, lang, band)
    parts = [r["head"], "", r["title"]]
    parts += [f"• {x}" for x in r["red"] + r["amber"]]
    parts += [f"ⓘ {x}" for x in r["note"]]
    if r["ask"]:
        parts += ["", r["ask_title"]] + [f"• {x}" for x in r["ask"]]
    parts += ["", r["foot"]]
    return "\n".join(parts)


def read_quote(data: bytes, media_type: str, client=None) -> tuple[dict, str]:
    client = client or boto3.client("bedrock-runtime", region_name=bill_reader.REGION)
    return bill_reader.call_first_enabled(client, bill_reader.tool_request(data, media_type, PROMPT, TOOL, max_tokens=1500))


def flags_dict(flags: list[Flag]) -> list[dict]:
    return [asdict(f) for f in flags]
