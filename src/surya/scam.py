"""Is this solar offer a scam? Checks a forwarded message, ad or call script for the usual signs.

The signs come from how PM Surya Ghar scams run in 2026: a 'processing fee' (applying on the portal
is free), promises of more subsidy than the scheme pays, 'free solar', pressure to decide today, a
big advance or cash, look-alike portal websites, requests for OTPs or bank details, claims of being
'government authorised', and imported panels sold as subsidy-eligible.
"""

from __future__ import annotations

import re

CENTRAL_MAX = 85800  # the highest central subsidy, in hill and North-East states
WITH_TOP_UP_MAX = 156000  # Delhi's top-up matches the central subsidy, the most any state adds

TEXT = {
    "en": {
        "fee": "It asks for a fee to register or process your subsidy. Applying on pmsuryaghar.gov.in is free; no one needs a fee for it.",
        "otp": "It asks for an OTP, Aadhaar or bank details. The scheme never collects these over a call or message.",
        "subsidy_high": "It promises {amount} of subsidy. The central subsidy is at most ₹78,000 (₹85,800 in hill and North-East states); only a few states add more. Ask which scheme pays the rest, in writing.",
        "subsidy_impossible": "It promises {amount} of subsidy, more than any home can get, even with a state top-up.",
        "free": "It offers 'free' solar. The subsidy is paid only after installation, and only Delhi currently offers ₹0 upfront, through registered vendors.",
        "urgency": "It pushes you to decide fast. That's the commonest scam tactic; the scheme runs till March 2027.",
        "advance": "It asks for {pct}% upfront. Pay at most 20–30% before the panels arrive, and tie the rest to delivery and commissioning.",
        "cash": "It asks for cash or a payment to a personal account. Pay only by bank transfer to the company, against a GST invoice.",
        "lookalike": "{domain} is not the official portal. Apply only at pmsuryaghar.gov.in.",
        "check_site": "It points to {domain}. The only official website is pmsuryaghar.gov.in.",
        "authorised": "It claims to be government-authorised. The ministry doesn't appoint sales agents; check the vendor's name in the registered list on pmsuryaghar.gov.in.",
        "non_dcr": "It offers imported or non-DCR panels with the subsidy. Imported panels don't get the subsidy.",
        "red": "🔴 This looks like a scam. Don't pay or share anything yet.",
        "amber": "🟠 Be careful with this offer.",
        "ok": "✅ No common scam signs found.",
        "always": "Always: check the vendor on pmsuryaghar.gov.in, never pay a 'processing fee', and pay in stages against a GST invoice.",
        "empty": "Paste or forward the message, ad or call details you want checked.",
    },
    "hi": {
        "fee": "यह सब्सिडी के पंजीकरण या प्रोसेसिंग की फ़ीस माँग रहा है। pmsuryaghar.gov.in पर आवेदन मुफ़्त है; इसके लिए किसी फ़ीस की ज़रूरत नहीं।",
        "otp": "यह OTP, आधार या बैंक की जानकारी माँग रहा है। योजना कभी कॉल या मैसेज पर ये नहीं माँगती।",
        "subsidy_high": "यह {amount} सब्सिडी का वादा कर रहा है। केंद्रीय सब्सिडी अधिकतम ₹78,000 है (पहाड़ी और पूर्वोत्तर राज्यों में ₹85,800); सिर्फ़ कुछ राज्य ही और देते हैं। बाकी पैसा कौन-सी योजना देगी, लिखित में पूछें।",
        "subsidy_impossible": "यह {amount} सब्सिडी का वादा कर रहा है, जो राज्य की अतिरिक्त सब्सिडी जोड़कर भी किसी घर को नहीं मिलती।",
        "free": "यह 'मुफ़्त' सोलर का ऑफ़र है। सब्सिडी इंस्टॉलेशन के बाद ही मिलती है, और अभी सिर्फ़ दिल्ली में रजिस्टर्ड वेंडर के ज़रिए ₹0 शुरुआती खर्च वाली योजना है।",
        "urgency": "यह जल्दी फ़ैसला करने का दबाव डाल रहा है। यह सबसे आम धोखा है; योजना मार्च 2027 तक चलेगी।",
        "advance": "यह {pct}% एडवांस माँग रहा है। पैनल आने से पहले 20–30% से ज़्यादा न दें, बाकी डिलीवरी और चालू होने से जोड़ें।",
        "cash": "यह नकद या निजी खाते में पैसे माँग रहा है। सिर्फ़ कंपनी के खाते में बैंक ट्रांसफ़र से, GST बिल के साथ भुगतान करें।",
        "lookalike": "{domain} आधिकारिक पोर्टल नहीं है। सिर्फ़ pmsuryaghar.gov.in पर आवेदन करें।",
        "check_site": "यह {domain} की तरफ़ भेज रहा है। आधिकारिक वेबसाइट सिर्फ़ pmsuryaghar.gov.in है।",
        "authorised": "यह सरकार से अधिकृत होने का दावा कर रहा है। मंत्रालय बिक्री एजेंट नियुक्त नहीं करता; pmsuryaghar.gov.in की रजिस्टर्ड सूची में वेंडर का नाम देखें।",
        "non_dcr": "यह सब्सिडी के साथ विदेशी या बिना DCR वाले पैनल दे रहा है। विदेशी पैनल पर सब्सिडी नहीं मिलती।",
        "red": "🔴 यह धोखा लग रहा है। अभी कोई पैसा या जानकारी न दें।",
        "amber": "🟠 इस ऑफ़र से सावधान रहें।",
        "ok": "✅ धोखे के आम संकेत नहीं मिले।",
        "always": "हमेशा: pmsuryaghar.gov.in पर वेंडर जाँचें, 'प्रोसेसिंग फ़ीस' कभी न दें, और GST बिल के साथ किस्तों में भुगतान करें।",
        "empty": "जिस मैसेज, विज्ञापन या कॉल की जाँच करनी है, उसे यहाँ चिपकाएँ या फ़ॉरवर्ड करें।",
    },
}

LEVEL = {"fee": "red", "otp": "red", "subsidy_impossible": "red", "lookalike": "red", "non_dcr": "red",
         "subsidy_high": "amber", "free": "amber", "urgency": "amber", "advance": "amber", "cash": "amber",
         "authorised": "amber", "check_site": "note"}

PATTERNS = {
    "fee": r"(registration|processing|booking|application|file|token|survey)\s*(fee|charge|charges|amount)|"
           r"(पंजीकरण|रजिस्ट्रेशन|प्रोसेसिंग|बुकिंग|फ़ाइल|फाइल)\s*(फ़ीस|फीस|शुल्क|चार्ज)",
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
        if re.search(pattern, low, re.I):
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
    for m in DOMAIN.finditer(low):
        domain = m.group(1).lower()
        if domain.endswith(("gov.in", "nic.in")):
            continue
        code = "lookalike" if re.search(r"surya|suryaghar|pmsg|muft|bijli|solar-?yojana", domain) else "check_site"
        found.append({"code": code, "values": {"domain": domain}})
        break
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
    return len(text) > 120 and bool(LOOKS_LIKE_OFFER.search(text)) and bool(check(text))
