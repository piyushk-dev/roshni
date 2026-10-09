"""Decision tools that work offline and do not collect identity documents."""

from __future__ import annotations

import calendar
import math
from datetime import date, datetime, timedelta, timezone

from . import knowledge, load_data
from .scheme import central_subsidy, emi

RESEARCH_DATE = "2026-10-08"
PORTAL = "https://pmsuryaghar.gov.in"
BANK = "https://sbi.bank.in/web/sbi-green/green-loans/personal/pm-surya-ghar-loan-for-solar-roof-top"


def today_india() -> date:
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).date()


def number(value, name: str, low: float, high: float) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if not math.isfinite(n) or not low <= n <= high:
        raise ValueError(f"{name} must be between {low:g} and {high:g}")
    return n


def state_code(value: str = "DL") -> str:
    code = str(value).strip().upper()
    if code not in load_data("schemes.json")["states"]:
        raise ValueError("choose a recognised state or union territory")
    return code


def schemes(state: str = "DL", kw: float = 3, dcr: str = "yes") -> dict:
    state = state_code(state)
    kw = number(kw, "system size", 0.5, 10)
    if dcr not in ("yes", "no", "not_stated"):
        raise ValueError("DCR must be yes, no or not_stated")
    catalog = load_data("schemes.json")
    special = state in catalog["special_category_states"]
    facts = {f["id"]: f for f in knowledge.facts(state)}
    cards = []
    for s in catalog["schemes"]:
        if s["scope"] not in ("IN", state, "SPECIAL" if special else "IN"):
            continue
        if special and s["id"] == "central":
            continue
        fact = facts.get(s.get("fact"), {})
        card = {**s, "source": s.get("source") or fact.get("source", PORTAL),
                      "checked_on": fact.get("verified", RESEARCH_DATE),
                      "status": fact.get("status", "needs_review"),
                      "official": fact.get("official", False)}
        if special and s["id"] == "society":
            card["amount"] = {"en": "₹19,800/kW for eligible common facilities in special-category regions, up to 500 kW and the 3 kW/household cap including residents’ individual plants.",
                              "hi": "विशेष श्रेणी में पात्र साझा सुविधाओं के लिए ₹19,800/kW; 500 kW तथा हर घर की 3 kW सीमा लागू, निजी सिस्टम भी शामिल।"}
            card["source"] = "https://mnre.gov.in/notice/operational-guidelines-for-implementation-of-the-component-central-financial-assistance-to-residential-consumers-of-pm-surya-ghar-muft-bijli-yojana/"
            card["calc"] = {**s["calc"], "per_kw": 19800}
        cards.append(card)
    potential = round(central_subsidy(kw, state)) if dcr != "no" else 0
    return {"states": catalog["states"], "state": state, "kw": kw, "special": special, "schemes": cards,
            "central_rs": potential if dcr == "yes" else 0, "potential_central_rs": potential,
            "eligibility": "no_dcr" if dcr == "no" else "evidence_needed" if dcr != "yes" else "subject_to_approval",
            "state_topup_included_rs": 0,
            "topup_reviewed": any(s["scope"] == state for s in cards),
            "note": {"en": "Central assistance is conditional on a residential grid-connected installation, registered installer, domestic cells and modules, and approval. State help is shown separately; confirm eligibility before budgeting it.",
                     "hi": "केंद्रीय सहायता आवासीय ग्रिड कनेक्शन, रजिस्टर्ड वेंडर, देश में बने सेल और मॉड्यूल तथा मंज़ूरी पर निर्भर है। राज्य की सहायता अलग दिखाई गई है; बजट में जोड़ने से पहले पात्रता की पुष्टि करें।"}}


def finance(body: dict) -> dict:
    cost = number(body.get("cost_rs", 195000), "project cost", 10000, 5000000)
    kw = number(body.get("kw", 3), "system size", 0.5, 10)
    state = state_code(body.get("state", "DL"))
    dcr = body.get("dcr", "not_stated")
    if dcr not in ("yes", "no", "not_stated"):
        raise ValueError("DCR must be yes, no or not_stated")
    margin = number(body.get("margin_pct", 10), "margin", 10, 100)
    years = number(body.get("years", 10), "loan years", 1, 10)
    delay = number(body.get("delay_months", 3), "subsidy wait", 0, 12)
    savings = number(body.get("monthly_saving_rs", 0), "monthly saving", 0, 100000)
    if int(years) != years or int(delay) != delay:
        raise ValueError("years and subsidy wait must be whole numbers")
    principal = cost * (1 - margin / 100)
    default_rate = 5.75 if principal <= 200000 else 7.90
    rate = number(body.get("rate_pct", default_rate), "interest rate", 0, 30)
    payment = emi(principal, rate, int(years))
    eligible_subsidy = central_subsidy(kw, state) if dcr == "yes" else 0
    balance = principal
    interest = 0
    for _ in range(int(delay)):
        monthly_interest = balance * rate / 1200
        interest += monthly_interest
        balance = max(0, balance + monthly_interest - payment)
    subsidy = min(balance, eligible_subsidy)
    after = max(0, balance - subsidy)
    remaining_months = int(years) * 12 - int(delay)
    r = rate / 1200
    recast = (after / remaining_months if r == 0 else after * r * (1+r)**remaining_months / ((1+r)**remaining_months-1)) if remaining_months and after else 0
    return {"cost_rs": round(cost), "cash_before_install_rs": round(cost-principal), "principal_rs": round(principal),
            "central_prepayment_rs": round(subsidy), "potential_central_rs": round(eligible_subsidy),
            "state": state, "kw": kw, "dcr": dcr, "monthly_saving_rs": round(savings),
            "rate_pct": rate, "years": int(years), "delay_months": int(delay),
            "emi_before_rs": round(payment), "emi_after_rs": round(recast), "interest_during_wait_rs": round(interest),
            "cash_during_wait_rs": round(cost-principal + payment*delay),
            "net_monthly_before_rs": round(savings-payment), "net_monthly_after_rs": round(savings-recast),
            "within_sbi_limit": principal <= 600000, "source": BANK, "checked_on": RESEARCH_DATE,
            "note": {"en": "Illustration: floating interest, no moratorium, monthly payments, and an approved central subsidy used to prepay the loan. A lower EMI requires lender recasting; otherwise tenure may shorten. State subsidies and battery costs are excluded. Loan approval and subsidy timing vary.",
                     "hi": "यह उदाहरण बदलती ब्याज दर, बिना मोरेटोरियम और मंज़ूर केंद्रीय सब्सिडी से लोन घटाने पर आधारित है। EMI घटाने के लिए बैंक को लोन दोबारा गणना करना होगा; वरना अवधि घट सकती है। राज्य सहायता और बैटरी खर्च शामिल नहीं हैं। मंज़ूरी और भुगतान का समय अलग हो सकता है।"}}


def care(body: dict) -> dict:
    """Compare like-for-like full months; a low result is evidence, not a fault diagnosis."""
    kw = number(body.get("kw", 3), "system size", 0.5, 500)
    period = str(body.get("month", ""))
    today = today_india()
    try:
        start = date.fromisoformat(period + "-01")
    except ValueError:
        raise ValueError("month must be YYYY-MM") from None
    if start > today.replace(day=1):
        raise ValueError("choose a completed month")
    days = calendar.monthrange(start.year, start.month)[1]
    if start == today.replace(day=1):
        raise ValueError("use a completed month so periods match")
    actual = number(body.get("actual_kwh"), "actual generation", 0, 1000000)
    promised = number(body.get("promised_kwh"), "promised generation for this month", 1, 1000000)
    last_clean = body.get("last_cleaned")
    days_clean = None
    if last_clean:
        try:
            clean_date = date.fromisoformat(str(last_clean))
        except ValueError:
            raise ValueError("cleaning date must be YYYY-MM-DD") from None
        if clean_date > today:
            raise ValueError("cleaning date cannot be in the future")
        days_clean = (today-clean_date).days
    pct = round(actual / promised * 100)
    shortfall = max(0, promised-actual)
    return {"month": period, "days": days, "kw": kw, "actual_kwh": actual, "promised_kwh": promised,
            "pct": pct, "shortfall_kwh": round(shortfall, 1), "days_since_clean": days_clean, "last_cleaned": last_clean or None,
            "status": "review" if actual / promised < 0.9 else "on_track", "cleaning_review": days_clean is None or days_clean > 30,
            "next": {"en": "Check outages, weather, shading and inverter errors before attributing a shortfall to dust. Ask your installer for the written guarantee, exclusions and service log. Schedule safe professional cleaning if needed.",
                     "hi": "कमी को धूल से जोड़ने से पहले बिजली कटौती, मौसम, छाया और इन्वर्टर की त्रुटि देखें। वेंडर से लिखित गारंटी, शर्तें और सर्विस रिकॉर्ड माँगें। ज़रूरत हो तो प्रशिक्षित व्यक्ति से सुरक्षित सफ़ाई करवाएँ।"},
            "draft": {"en": f"Subject: Solar generation review for {period}\n\nHello, my {kw:g} kW system generated {actual:g} kWh in {period}, compared with the written monthly estimate of {promised:g} kWh ({pct}% achieved). Please review the inverter logs, outages and maintenance history, explain the difference, and confirm the next service date. I can attach the monthly generation screenshot, agreement and service records. Please confirm any guarantee exclusions and the remedy in writing.",
                      "hi": f"विषय: {period} के सोलर उत्पादन की जाँच\n\nनमस्ते, मेरे {kw:g} kW सिस्टम ने {period} में {actual:g} kWh बनाए, जबकि लिखित मासिक अनुमान {promised:g} kWh था ({pct}% पूरा)। कृपया इन्वर्टर लॉग, कटौती और रखरखाव की जाँच करके अंतर का कारण और अगली सर्विस की तारीख बताएँ। मासिक स्क्रीनशॉट, एग्रीमेंट और सर्विस रिकॉर्ड संलग्न कर सकता/सकती हूँ। गारंटी की शर्तें और समाधान लिखित में बताएँ।"}}


def checklists() -> dict:
    return {**load_data("checklists.json"), "support_topics": load_data("support.json")["topics"]}


def support(body: dict) -> dict:
    """Prepare evidence and a neutral request; never file a complaint or infer liability."""
    topics = {topic["id"]: topic for topic in load_data("support.json")["topics"]}
    kind = body.get("kind")
    if not isinstance(kind, str) or kind not in topics:
        raise ValueError("choose a recognised support issue")
    today = today_india()

    def past_date(value, name):
        try:
            parsed = date.fromisoformat(str(value))
        except ValueError:
            raise ValueError(f"{name} must be YYYY-MM-DD") from None
        if parsed.isoformat() != value or parsed > today:
            raise ValueError(f"{name} must be a valid date no later than today")
        return parsed

    noticed = past_date(body.get("first_noticed"), "first noticed date")
    contact = past_date(body["contacted_on"], "contact date") if body.get("contacted_on") else None
    if contact and contact < noticed:
        raise ValueError("contact date cannot precede the first noticed date")
    topic = topics[kind]
    days = (today-contact).days if contact else None
    draft = {}
    for lang in ("en", "hi"):
        chronology = (f"First noticed: {noticed.isoformat()}. Last contacted: {contact.isoformat() if contact else 'not recorded'}." if lang == "en" else
                      f"पहली बार देखा: {noticed.isoformat()}। आख़िरी संपर्क: {contact.isoformat() if contact else 'दर्ज नहीं'}।")
        request = ("Please acknowledge this request with a ticket number and confirm the next action and expected date in writing." if lang == "en" else
                   "कृपया टिकट नंबर से पावती दें और अगला कदम व अनुमानित तारीख लिखित में दें।")
        asks = {
            "monitoring": {"en": "Please compare communication logs with generation readings, explain the monitoring problem and confirm logger coverage and any proposed charges before work starts.", "hi": "कृपया संचार लॉग और उत्पादन रीडिंग मिलाएँ, ऐप की समस्या समझाएँ और काम से पहले लॉगर की वारंटी तथा किसी शुल्क की पुष्टि करें।"},
            "generation": {"en": "Please review matching-period generation, inverter errors and outages against the written estimate, and identify applicable service or guarantee terms and exclusions.", "hi": "समान अवधि के उत्पादन, इन्वर्टर त्रुटि और कटौती को लिखित अनुमान से मिलाएँ तथा लागू सर्विस/गारंटी और अपवाद बताएँ।"},
            "billing": {"en": "Please provide the import/export statement for the matching bill dates, explain carried credits and settlement rules, and confirm any required bill correction in writing.", "hi": "कृपया बिल की समान तारीखों का आयात/निर्यात विवरण, पुराने क्रेडिट और भुगतान नियम समझाएँ तथा ज़रूरी बिल सुधार लिखित में बताएँ।"},
            "documents": {"en": "Please provide the missing handover documents with matching equipment serials and confirm whether any portal record needs correction.", "hi": "गायब हैंडओवर दस्तावेज़ उपकरण के मिलते सीरियल के साथ दें और बताएँ कि पोर्टल रिकॉर्ड में सुधार चाहिए या नहीं।"},
            "maintenance": {"en": "Please confirm visits and repairs included in the signed maintenance agreement, the record of completed visits, and any proposed charges before service starts.", "hi": "हस्ताक्षर वाले रखरखाव एग्रीमेंट की शामिल विज़िट/मरम्मत, पूरी हुई विज़िट और सर्विस से पहले किसी प्रस्तावित शुल्क की पुष्टि करें।"},
        }
        request += " " + asks[kind][lang]
        heading = "Evidence to attach" if lang == "en" else "लगाने वाले प्रमाण"
        draft[lang] = f"{topic['title'][lang]}\n\n{chronology}\n\n{request}\n\n{heading}:\n" + "\n".join("• "+item[lang] for item in topic["evidence"])
    return {**topic, "first_noticed": noticed.isoformat(), "contacted_on": contact.isoformat() if contact else None,
            "days_since_contact": days, "prepared_on": today.isoformat(), "draft": draft, "checked_on": RESEARCH_DATE,
            "help_source": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2245159&lang=2&reg=48",
            "portal": PORTAL,
            "note": {"en": "This prepares a request; it does not open a service ticket or submit a complaint. Days since contact are a personal record, not an official response deadline. Review the note and send it through the recipient's official channel. Keep sensitive account and identity documents out of public messages.",
                     "hi": "इससे अनुरोध तैयार होता है; टिकट या शिकायत जमा नहीं होती। संपर्क के बाद दिन आपका रिकॉर्ड है, आधिकारिक जवाब की समय सीमा नहीं। नोट जाँचकर सही आधिकारिक चैनल से खुद भेजें। सार्वजनिक संदेश में खाता या पहचान दस्तावेज़ न डालें।"}}


def bill_balance(body: dict) -> dict:
    """Explain energy flows, without assuming one state's monetary settlement rules."""
    generation = number(body.get("generation_kwh"), "generation", 0, 1000000)
    imported = number(body.get("import_kwh"), "grid import", 0, 1000000)
    exported = number(body.get("export_kwh"), "grid export", 0, generation)
    credited = number(body.get("bill_export_kwh"), "export shown on bill", 0, 1000000)
    missing = max(0, exported-credited)
    difference = exported-credited
    return {"self_consumed_kwh": round(generation-exported, 1),
            "generation_kwh": generation, "import_kwh": imported,
            "export_kwh": exported, "bill_export_kwh": credited,
            "household_use_kwh": round(generation-exported+imported, 1),
            "net_grid_kwh": round(imported-exported, 1), "export_difference_kwh": round(missing, 1),
            "meter_bill_difference_kwh": round(difference, 1),
            "status": "review" if abs(difference) > 1 else "matched",
            "note": {"en": "Use readings for the same billing dates and a system without battery storage. Generation is not export. A positive difference means meter export exceeds bill export; a negative one means the reverse. Check periods and carried credits. These are energy balances, not a bill calculation; banking, fixed charges and settlement follow your DISCOM’s rules. A mismatch needs review, not an automatic refund.",
                     "hi": "एक ही बिल अवधि की रीडिंग और बिना बैटरी वाला सिस्टम लें। उत्पादन और निर्यात अलग हैं। धनात्मक अंतर में मीटर का निर्यात बिल से ज़्यादा है; ऋणात्मक में उलटा। अवधि और पुराने क्रेडिट जाँचें। यह ऊर्जा का हिसाब है, रुपये का बिल नहीं; बैंकिंग और भुगतान बिजली कंपनी के नियमों से तय होंगे। अंतर पर जाँच चाहिए, अपने-आप रिफंड नहीं।"}}


# --- dust and smog: when to clean the panels ----------------------------------------------------
# Delhi's dust cuts output by 0.3-0.6% a day (EU PVSEC 2018 study); cleaning is worth doing after
# a dusty spell, not during one. The forecast is CAMS data served free by Open-Meteo.
DUST_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
DUST_SOURCE = "https://open-meteo.com/en/docs/air-quality-api"
DUST_CACHE_S = 3 * 3600
DELHI = (28.6, 77.2)
_dust_cache: dict[tuple[float, float, str], tuple[float, dict]] = {}


def _fetch_json(url: str) -> dict:
    import json
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "surya-saathi"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def dust(lat=None, lon=None, fetch=None, now: float | None = None) -> dict:
    """Five days of PM10 and dust for a place from today, and the first clear day after the dust settles."""
    import time

    lat = round(number(lat if lat not in (None, "") else DELHI[0], "latitude", 6, 38), 1)
    lon = round(number(lon if lon not in (None, "") else DELHI[1], "longitude", 68, 98), 1)
    now = now or time.time()
    today = datetime.fromtimestamp(now, timezone(timedelta(hours=5, minutes=30))).date().isoformat()
    hit = _dust_cache.get((lat, lon, today))
    if hit and now - hit[0] < DUST_CACHE_S:
        return hit[1]
    raw = (fetch or _fetch_json)(f"{DUST_URL}?latitude={lat}&longitude={lon}&hourly=pm10,dust&timezone=Asia%2FKolkata&forecast_days=6")
    hours = raw["hourly"]
    by_day: dict[str, dict[str, list[float]]] = {}
    for t, pm, du in zip(hours["time"], hours["pm10"], hours["dust"]):
        day = by_day.setdefault(t[:10], {"pm10": [], "dust": []})
        if pm is not None:
            day["pm10"].append(pm)
        if du is not None:
            day["dust"].append(du)
    days = []
    for d, v in sorted(by_day.items()):
        # a forecast cached across midnight still starts yesterday, and the last day is only part-filled
        if d < today or len(v["pm10"]) < 18:
            continue
        pm = round(sum(v["pm10"]) / len(v["pm10"])) if v["pm10"] else None
        du = round(max(v["dust"])) if v["dust"] else None
        # India's National AQI bands for 24-hour PM10: up to 100 satisfactory, 101-250 moderate, above 250 poor
        level = "high" if (pm or 0) > 250 else "dusty" if (pm or 0) > 100 else "clear"
        days.append({"date": d, "pm10": pm, "dust_max": du, "level": level})
    days = days[:5]
    if not days:
        raise OSError("the forecast has no days from today")
    dusty = [i for i, d in enumerate(days) if d["level"] != "clear"]
    if not dusty:
        advice, clean = "clear_week", None
    elif dusty[-1] == len(days) - 1:
        # dust returns by the end; a low day between dusty ones is worth it only if the panels look dirty
        lulls = [d["date"] for d in days if d["level"] == "clear"]
        advice, clean = ("clean_lull", lulls[-1]) if lulls else ("dusty_week", None)
    else:
        advice, clean = "clean_after", days[dusty[-1] + 1]["date"]
    result = {"lat": lat, "lon": lon, "days": days, "advice": advice, "clean_on": clean, "source": DUST_SOURCE}
    _dust_cache[(lat, lon, today)] = (now, result)
    return result


DUST_TEXT = {
    "en": {"head": "🌫️ Dust and smog near you, next {n} days:", "clear": "low", "dusty": "dusty", "high": "very dusty",
           "row": "{day}: {level} (PM10 {pm} µg/m³)",
           "clean_after": "🧽 Clean the panels on {day}, after the dust settles. Use plain water early in the morning; never spray the inverter.",
           "dusty_week": "🧽 Dust stays high all week. Wait for a clear day to clean, or the panels just get dusty again.",
           "clean_lull": "🧽 Dust dips on {day}, then rises again. If the panels look dirty, clean that morning with plain water; otherwise wait for a settled spell.",
           "clear_week": "🧽 Low dust this week, so your usual cleaning schedule is fine.",
           "why": "Dust in Delhi can cut solar output by 0.3–0.6% a day."},
    "hi": {"head": "🌫️ आपके इलाके में अगले {n} दिन धूल और स्मॉग:", "clear": "कम", "dusty": "धूल", "high": "बहुत धूल",
           "row": "{day}: {level} (PM10 {pm} µg/m³)",
           "clean_after": "🧽 {day} को पैनल साफ़ करें, धूल बैठने के बाद। सुबह-सुबह सादे पानी से; इन्वर्टर पर कभी पानी न डालें।",
           "dusty_week": "🧽 पूरे हफ़्ते धूल ज़्यादा रहेगी। साफ़ दिन का इंतज़ार करें, वरना पैनल फिर धूल से भर जाएँगे।",
           "clean_lull": "🧽 {day} को धूल कुछ कम होगी, फिर बढ़ेगी। पैनल गंदे दिखें तो उस सुबह सादे पानी से साफ़ करें; वरना धूल थमने का इंतज़ार करें।",
           "clear_week": "🧽 इस हफ़्ते धूल कम है, सफ़ाई का सामान्य समय ठीक है।",
           "why": "दिल्ली में धूल से सोलर उत्पादन रोज़ 0.3–0.6% घट सकता है।"},
}


def dust_message(result: dict, lang: str = "en") -> str:
    t = DUST_TEXT[lang if lang in DUST_TEXT else "en"]
    label = lambda iso: date.fromisoformat(iso).strftime("%a %d %b")
    lines = [t["head"].format(n=len(result["days"]))]
    lines += [t["row"].format(day=label(d["date"]), level=t[d["level"]], pm=d["pm10"] if d["pm10"] is not None else "?") for d in result["days"]]
    lines += ["", t[result["advice"]].format(day=label(result["clean_on"]) if result["clean_on"] else ""), t["why"]]
    return "\n".join(lines)
