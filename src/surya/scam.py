"""Is this solar offer a scam? Checks a forwarded message, ad or call script for the usual signs.

The signs come from how PM Surya Ghar scams run in 2026: a 'processing fee' (applying on the portal
is free), promises of more subsidy than the scheme pays, 'free solar', pressure to decide today, a
big advance or cash, look-alike portal websites, requests for OTPs or bank details, claims of being
'government authorised', and imported panels sold as subsidy-eligible.
"""

from __future__ import annotations

import re

CENTRAL_MAX = 85800  # the highest central subsidy, in hill and North-East states
WITH_TOP_UP_MAX = 156000  # a reviewed comparison threshold, not a universal subsidy cap

TEXT = {
    "en": {
        "fee": "It asks for a fee to register or process your subsidy. Applying on pmsuryaghar.gov.in is free; no one needs a fee for it.",
        "otp": "It mentions an OTP, Aadhaar or bank details. Do not share authentication codes with a caller or salesperson. Use the relevant official secure portal for required documents.",
        "service_fee": "It mentions a survey, booking or token fee. This is not proof of fraud: ask what service it buys, whether it is refundable, and how it appears in the written project price. National-portal application is free.",
        "subsidy_high": "It promises {amount} of subsidy. The central subsidy is at most ₹78,000 (₹85,800 in hill and North-East states); only a few states add more. Ask which scheme pays the rest, in writing.",
        "subsidy_impossible": "It promises {amount} of subsidy, above the central cap and the common top-ups in our reviewed data. Ask for the applicable government order and eligibility; do not budget this claim yet.",
        "free": "It offers 'free' solar. A subsidy, loan, or utility-led scheme may reduce upfront payment, but has different conditions. Ask who owns the plant, who pays, and whether an EMI remains.",
        "urgency": "It pushes you to decide fast. That's the commonest scam tactic; the scheme runs till March 2027.",
        "advance": "It asks for {pct}% upfront. Pay at most 20–30% before the panels arrive, and tie the rest to delivery and commissioning.",
        "cash": "It asks for cash or a payment to a personal account. Pay only by bank transfer to the company, against a GST invoice.",
        "lookalike": "{domain} resembles the scheme's name but is not the National Portal domain. Verify its purpose and ownership through a government source before submitting documents or paying.",
        "check_site": "{domain} has not been verified by this check. Installer, bank and state/DISCOM websites may be legitimate; confirm the exact link through their independently sourced official website. The National Portal is pmsuryaghar.gov.in.",
        "authorised": "It claims to be government-authorised. The ministry doesn't appoint sales agents; check the vendor's name in the registered list on pmsuryaghar.gov.in.",
        "non_dcr": "It offers imported or non-DCR panels with the subsidy. Imported panels don't get the subsidy.",
        "red": "🔴 Serious warning signs. Verify the offer before paying or sharing sensitive information.",
        "amber": "🟠 Be careful with this offer.",
        "ok": "No common warning signs found. This does not verify the sender or the offer.",
        "always": "Always: check the vendor on pmsuryaghar.gov.in, never pay a 'processing fee', and pay in stages against a GST invoice.",
        "empty": "Paste or forward the message, ad or call details you want checked.",
    },
    "hi": {
        "fee": "यह सब्सिडी के पंजीकरण या प्रोसेसिंग की फ़ीस माँग रहा है। pmsuryaghar.gov.in पर आवेदन मुफ़्त है; इसके लिए किसी फ़ीस की ज़रूरत नहीं।",
        "otp": "इसमें OTP, आधार या बैंक की जानकारी का उल्लेख है। कॉल करने वाले या सेल्स व्यक्ति को सुरक्षा कोड न दें। ज़रूरी दस्तावेज़ संबंधित सुरक्षित आधिकारिक पोर्टल पर दें।",
        "service_fee": "इसमें सर्वे, बुकिंग या टोकन फ़ीस है। यह अपने-आप धोखे का प्रमाण नहीं: कौन सी सेवा, रिफंड की शर्त और लिखित कुल कीमत में इसका हिस्सा पूछें। राष्ट्रीय पोर्टल का आवेदन मुफ़्त है।",
        "subsidy_high": "यह {amount} सब्सिडी का वादा कर रहा है। केंद्रीय सब्सिडी अधिकतम ₹78,000 है (पहाड़ी और पूर्वोत्तर राज्यों में ₹85,800); सिर्फ़ कुछ राज्य ही और देते हैं। बाकी पैसा कौन-सी योजना देगी, लिखित में पूछें।",
        "subsidy_impossible": "यह {amount} सब्सिडी का दावा है, जो केंद्रीय सीमा और हमारी जाँची सामान्य राज्य सहायता से अधिक है। लागू सरकारी आदेश और पात्रता माँगें; अभी बजट में न जोड़ें।",
        "free": "यह 'मुफ़्त' सोलर का ऑफ़र है। सब्सिडी, लोन या बिजली कंपनी वाली योजना की अलग शर्तें होती हैं। मालिक कौन होगा, भुगतान कौन करेगा और EMI बचेगी या नहीं, पूछें।",
        "urgency": "यह जल्दी फ़ैसला करने का दबाव डाल रहा है। यह सबसे आम धोखा है; योजना मार्च 2027 तक चलेगी।",
        "advance": "यह {pct}% एडवांस माँग रहा है। पैनल आने से पहले 20–30% से ज़्यादा न दें, बाकी डिलीवरी और चालू होने से जोड़ें।",
        "cash": "यह नकद या निजी खाते में पैसे माँग रहा है। सिर्फ़ कंपनी के खाते में बैंक ट्रांसफ़र से, GST बिल के साथ भुगतान करें।",
        "lookalike": "{domain} योजना के नाम जैसा है, पर राष्ट्रीय पोर्टल का डोमेन नहीं। दस्तावेज़ या पैसा देने से पहले सरकारी स्रोत से इसका उद्देश्य और मालिक जाँचें।",
        "check_site": "इस जाँच ने {domain} की पुष्टि नहीं की। वेंडर, बैंक और राज्य/बिजली कंपनी की साइट सही हो सकती है; स्वतंत्र आधिकारिक स्रोत से सही लिंक मिलाएँ। राष्ट्रीय पोर्टल pmsuryaghar.gov.in है।",
        "authorised": "यह सरकार से अधिकृत होने का दावा कर रहा है। मंत्रालय बिक्री एजेंट नियुक्त नहीं करता; pmsuryaghar.gov.in की रजिस्टर्ड सूची में वेंडर का नाम देखें।",
        "non_dcr": "यह सब्सिडी के साथ विदेशी या बिना DCR वाले पैनल दे रहा है। विदेशी पैनल पर सब्सिडी नहीं मिलती।",
        "red": "🔴 गंभीर चेतावनी के संकेत। पैसा या संवेदनशील जानकारी देने से पहले पुष्टि करें।",
        "amber": "🟠 इस ऑफ़र से सावधान रहें।",
        "ok": "आम चेतावनी के संकेत नहीं मिले। इससे भेजने वाले या ऑफ़र की पुष्टि नहीं होती।",
        "always": "हमेशा: pmsuryaghar.gov.in पर वेंडर जाँचें, 'प्रोसेसिंग फ़ीस' कभी न दें, और GST बिल के साथ किस्तों में भुगतान करें।",
        "empty": "जिस मैसेज, विज्ञापन या कॉल की जाँच करनी है, उसे यहाँ चिपकाएँ या फ़ॉरवर्ड करें।",
    },
}

LEVEL = {"fee": "red", "otp": "red", "subsidy_impossible": "red", "lookalike": "red", "non_dcr": "red",
         "subsidy_high": "amber", "free": "amber", "urgency": "amber", "advance": "amber", "cash": "amber",
         "authorised": "amber", "service_fee": "amber", "check_site": "note"}

PATTERNS = {
    "fee": r"(registration|processing|application|file)\s*(fee|charge|charges|amount)|"
           r"(पंजीकरण|रजिस्ट्रेशन|प्रोसेसिंग|फ़ाइल|फाइल)\s*(फ़ीस|फीस|शुल्क|चार्ज)",
    "service_fee": r"(survey|booking|token)\s*(fee|charge|charges|amount)|"
                   r"(सर्वे|बुकिंग|टोकन)\s*(फ़ीस|फीस|शुल्क|चार्ज)",
    "otp": r"\botp\b|aadhaar|aadhar|आधार|\bcvv\b|\bpin number\b|bank details|account number|खाता नंबर|बैंक डिटेल",
    "free": r"free solar|free (panels?|installation|rooftop)|muft|मुफ्त|मुफ़्त|zero cost|no cost|0 cost|बिल्कुल फ्री|फ्री सोलर",
    "urgency": r"today only|last (date|day|chance)|limited (slots?|offer|period|time)|hurry|offer ends|expires today|only \d+ slots|"
               r"जल्दी करें|आज ही|आखिरी मौका|आख़िरी मौका|सीमित",
    "cash": r"\bcash\b|नकद|personal account|my account|निजी खाते",
    "authorised": r"(mnre|government|govt|sarkar|sarkari|सरकार|सरकारी)\W+(\w+\W+)?(authori[sz]ed|approved|appointed|agent|अधिकृत|मान्यता)",
    "non_dcr": r"imported panels?|chinese panels?|non[- ]?dcr|विदेशी पैनल|चाइनीज़ पैनल|चाइनीज पैनल",
}
SUBSIDY_WORD = re.compile(r"subsid|सब्सिडी|अनुदान", re.I)
AMOUNT = re.compile(r"(₹|rs\.?|inr|रु\.?)?\s*(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*(lakh|lac|लाख|thousand|हज़ार|हजार|k\b)?", re.I)
ADVANCE = re.compile(r"(\d{2,3})\s*%\s*(advance|upfront|पहले|एडवांस)|(advance|upfront|एडवांस)\D{0,15}(\d{2,3})\s*%|"
                     r"(full|पूरा|100%)\s*(payment|advance|भुगतान)\s*(advance|upfront|पहले)?", re.I)
DOMAIN = re.compile(r"(?:https?://)?(?:www\.)?((?:[a-z0-9-]+\.)+(?:gov\.in|nic\.in|co\.in|org\.in|com|in|org|net|info|online|site|xyz))\b", re.I)


def _rupees(num: str, unit: str | None, currency: str | None) -> float | None:
    value = float(num.replace(",", ""))
    unit = (unit or "").lower()
    if unit in ("lakh", "lac", "लाख"):
        return value * 100000
    if unit in ("thousand", "हज़ार", "हजार", "k"):
        return value * 1000
    return value if (currency or value >= 10000) else None


def _subsidy_claims(text: str) -> list[float]:
    out = []
    for m in SUBSIDY_WORD.finditer(text):
        window = text[max(0, m.start() - 60): m.end() + 60]
        for a in AMOUNT.finditer(window):
            value = _rupees(a.group(2), a.group(3), a.group(1))
            if value and 1000 <= value <= 5e7:
                out.append(value)
    return out


def check(text: str) -> list[dict]:
    """Every scam sign found in the text, as {code, level, values}."""
    found: list[dict] = []
    low = text.lower()
    for code, pattern in PATTERNS.items():
        matches = list(re.finditer(pattern, low, re.I))
        positive = []
        for m in matches:
            before = low[max(0, m.start()-45):m.start()]
            after = low[m.end():m.end()+25]
            if code in ("fee", "service_fee", "otp", "cash", "non_dcr"):
                if re.search(r"(?:no|nil|zero|never|avoid|do not|don't)\s+(?:\w+\s+){0,4}$", before):
                    continue
                if re.search(r"(?:न दें|न भेजें|न बताएँ|नहीं|मत भेज)", after):
                    continue
                if code in ("fee", "service_fee") and re.match(r"\s*[:=–-]?\s*(?:₹|rs\.?|inr)?\s*(?:0(?:\.0+)?(?!\d|\.\d)|nil\b|zero\b)", after):
                    continue
            positive.append(m)
        if positive:
            found.append({"code": code, "values": {}})
    claims = _subsidy_claims(text)
    if claims:
        top = max(claims)
        from .format import inr

        if top > WITH_TOP_UP_MAX:
            found.append({"code": "subsidy_impossible", "values": {"amount": inr(top)}})
        elif top > CENTRAL_MAX:
            found.append({"code": "subsidy_high", "values": {"amount": inr(top)}})
    for m in ADVANCE.finditer(low):
        pct = 100 if m.group(5) else int(m.group(1) or m.group(4))
        if pct > 30:
            found.append({"code": "advance", "values": {"pct": pct}})
            break
    seen = set()
    for m in DOMAIN.finditer(low):
        domain = m.group(1).lower()
        if domain in seen:
            continue
        seen.add(domain)
        if domain.endswith((".gov.in", ".nic.in")):
            continue
        code = "lookalike" if re.search(r"suryaghar|pmsg|muft-?bijli|solar-?yojana", domain) else "check_site"
        found.append({"code": code, "values": {"domain": domain}})
    for f in found:
        f["level"] = LEVEL[f["code"]]
    return found


def verdict(found: list[dict]) -> str:
    levels = {f["level"] for f in found}
    return "red" if "red" in levels else "amber" if "amber" in levels else "ok"


def render(found: list[dict], lang: str = "en") -> dict:
    t = TEXT[lang if lang in TEXT else "en"]
    v = verdict(found)
    order = {"red": 0, "amber": 1, "note": 2}
    return {"verdict": v, "title": t[v], "signs": [t[f["code"]].format(**f["values"]) for f in sorted(found, key=lambda f: order[f["level"]])],
            "always": t["always"]}


def message(text: str, lang: str = "en") -> str:
    if not text.strip():
        return TEXT[lang if lang in TEXT else "en"]["empty"]
    r = render(check(text), lang)
    return "\n".join([r["title"], *[f"• {s}" for s in r["signs"]], "", r["always"]])


LOOKS_LIKE_OFFER = re.compile(r"solar|सोलर|surya ghar|सूर्य घर|subsid|सब्सिडी|rooftop|panel|पैनल", re.I)


def looks_like_offer(text: str) -> bool:
    """A forwarded solar ad or offer, as opposed to a question for the bot."""
    return len(text) > 120 and bool(LOOKS_LIKE_OFFER.search(text)) and any(f["level"] in ("red", "amber") for f in check(text))
