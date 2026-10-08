"""WhatsApp-ready summaries of an Analysis, in English and Hindi."""

from __future__ import annotations

from .calculator import ECON, Analysis


def inr(x: float) -> str:
    """Rupees with Indian digit grouping: 195000 -> ₹1,95,000."""
    n = int(round(x))
    digits = str(abs(n))
    if len(digits) > 3:
        head, groups = digits[:-3], [digits[-3:]]
        while head:
            groups.insert(0, head[-2:])
            head = head[:-2]
        digits = ",".join(groups)
    return f"{'-' if n < 0 else ''}₹{digits}"


def _hundreds(x: float) -> str:
    return inr(round(x, -2))


REASONS = {
    "covers": {
        "en": "This makes about {cover}% of the electricity you use in a year.",
        "hi": "इससे आपकी सालाना खपत की लगभग {cover}% बिजली बनेगी।",
    },
    "subsidy_covers": {
        "en": "You use {free:g} units or fewer in most months, so the state subsidy already keeps your bill near zero. Solar would add little.",
        "hi": "ज़्यादातर महीनों में आपकी खपत {free:g} यूनिट या उससे कम है, इसलिए सरकारी सब्सिडी से बिल पहले ही लगभग शून्य है। सोलर से ज़्यादा फ़ायदा नहीं होगा।",
    },
    "low_savings": {
        "en": "At your usage, solar wouldn't earn back its cost over 25 years.",
        "hi": "आपकी खपत पर सोलर 25 साल में भी अपनी लागत नहीं निकाल पाएगा।",
    },
    "roof_too_small": {
        "en": "Each kW needs about {per_kw} sq ft of shade-free roof, and you have {roof:g} sq ft.",
        "hi": "हर kW के लिए लगभग {per_kw} वर्ग फुट छाया-रहित छत चाहिए, और आपके पास {roof:g} वर्ग फुट है।",
    },
}

NOTES = {
    "dcr": {
        "en": "To get the subsidy, the panels must be made in India (DCR). Ask the vendor for the DCR certificate.",
        "hi": "सब्सिडी के लिए पैनल भारत में बने (DCR) होने चाहिए। वेंडर से DCR सर्टिफ़िकेट ज़रूर माँगें।",
    },
    "load_increase": {
        "en": "{kw:g} kW is above your sanctioned load of {load:g} kW. Most providers cap rooftop systems at sanctioned load, so you may need to apply for a load increase.",
        "hi": "{kw:g} kW आपके स्वीकृत लोड {load:g} kW से ज़्यादा है। ज़्यादातर कंपनियाँ सोलर को स्वीकृत लोड तक सीमित रखती हैं, इसलिए लोड बढ़वाने का आवेदन करना पड़ सकता है।",
    },
    "export_heavy": {
        "en": "About {export:,.0f} units a year would go to the grid unused, and those earn only about ₹{rate:g} each.",
        "hi": "सालाना लगभग {export:,.0f} यूनिट ग्रिड में बिना इस्तेमाल के जाएँगी, जिनके सिर्फ़ लगभग ₹{rate:g} प्रति यूनिट मिलते हैं।",
    },
    "estimated_months_temp": {
        "en": "Your bill showed {known} months of usage. We estimated the rest from how your usage rises with local temperature, so an older bill would sharpen this.",
        "hi": "आपके बिल में {known} महीनों की खपत थी। बाकी महीनों का अनुमान इससे लगाया गया कि गर्मी बढ़ने पर आपकी खपत कितनी बढ़ती है; पुराना बिल भेजेंगे तो अनुमान और सटीक होगा।",
    },
    "estimated_months": {
        "en": "Your bill showed {known} months of usage. We filled the rest with your average, so an older bill would sharpen this.",
        "hi": "आपके बिल में {known} महीनों की खपत थी। बाकी महीनों के लिए औसत लिया गया है; पुराना बिल भेजेंगे तो अनुमान और सटीक होगा।",
    },
}

GO = {
    "en": (
        "☀️ Solar estimate for your {discom} connection\n\n"
        "Best size: {kw:g} kW (needs about {roof_needed:,.0f} sq ft of shade-free roof)\n"
        "Cost: {gross} − {subsidy} subsidy = {net}\n"
        "Saves {save_low}–{save_high} a year, about {save_month} a month\n"
        "Pays for itself in {payback:.1f} years\n"
        "Loan: {emi}/month for 10 years at {rate:g}%, or {emi_after}/month once the subsidy is used to prepay\n"
        "Over 25 years: about {save_25} saved\n"
        "Avoids about {co2:.1f} tonnes of CO₂ a year\n\n"
        "{reason}\n"
        "We used the lower of two sunlight datasets, so real savings should be at or above this.\n"
        "Before you sign with any vendor, send me their quote and I'll check it."
    ),
    "hi": (
        "☀️ आपके {discom} कनेक्शन के लिए सोलर अनुमान\n\n"
        "सही साइज़: {kw:g} kW (लगभग {roof_needed:,.0f} वर्ग फुट छाया-रहित छत चाहिए)\n"
        "लागत: {gross} − {subsidy} सब्सिडी = {net}\n"
        "बचत: सालाना {save_low}–{save_high}, यानी लगभग {save_month} महीना\n"
        "{payback:.1f} साल में पूरी लागत वसूल\n"
        "लोन: 10 साल तक {emi}/महीना ({rate:g}% ब्याज), सब्सिडी से लोन घटाने पर {emi_after}/महीना\n"
        "25 साल में: लगभग {save_25} की बचत\n"
        "हर साल लगभग {co2:.1f} टन CO₂ कम\n\n"
        "{reason}\n"
        "हमने धूप के दो डेटा में से कम वाला लिया है, इसलिए असली बचत इससे कम नहीं होनी चाहिए।\n"
        "किसी भी वेंडर से साइन करने से पहले उनका कोटेशन यहाँ भेजें, उसकी जाँच हो जाएगी।"
    ),
}

SKIP = {
    "en": (
        "☀️ Solar check for your {discom} connection\n\n"
        "Honest answer: solar isn't worth it for you right now.\n"
        "{reason}\n"
        "Your bill now: about {bill_month} a month.\n\n"
        "If your usage goes up (a new AC, a bigger family), send a newer bill and I'll check again."
    ),
    "hi": (
        "☀️ आपके {discom} कनेक्शन की सोलर जाँच\n\n"
        "सच कहें तो: अभी सोलर आपके लिए फ़ायदेमंद नहीं है।\n"
        "{reason}\n"
        "अभी आपका बिल: लगभग {bill_month} महीना।\n\n"
        "अगर खपत बढ़े (नया AC, परिवार बड़ा हो), तो नया बिल भेजें, दोबारा जाँच हो जाएगी।"
    ),
}


PROBLEMS = {
    "file_type": {
        "en": "Please send the bill as a photo or a PDF.",
        "hi": "कृपया बिल फोटो या PDF के रूप में भेजें।",
    },
    "not_a_bill": {
        "en": "That doesn't look like an electricity bill. Please send a clear photo of the whole bill.",
        "hi": "यह बिजली का बिल नहीं लग रहा। कृपया पूरे बिल की साफ़ फोटो भेजें।",
    },
    "unsupported_provider": {
        "en": "Sorry, only Delhi bills work for now (BSES Rajdhani, BSES Yamuna, Tata Power-DDL). This one is from {provider}.",
        "hi": "माफ़ कीजिए, अभी सिर्फ़ दिल्ली के बिल (BSES राजधानी, BSES यमुना, टाटा पावर-DDL) पढ़े जा सकते हैं। यह बिल {provider} का है।",
    },
    "unreadable": {
        "en": "I couldn't read the sanctioned load or the usage history. Please send a clearer photo that shows the whole bill.",
        "hi": "बिल से स्वीकृत लोड या खपत का इतिहास पढ़ा नहीं जा सका। कृपया पूरे बिल की और साफ़ फोटो भेजें।",
    },
}


class BillProblem(ValueError):
    """Something about the bill the household can fix, with the reply to send them."""

    def __init__(self, code: str, **values):
        self.code, self.values = code, values
        super().__init__(self.text("en"))

    def text(self, lang: str) -> str:
        return PROBLEMS[self.code][lang if lang in ("en", "hi") else "en"].format(**self.values)


def explain(a: Analysis, lang: str = "en") -> tuple[str, list[str]]:
    """The verdict's reason and the notes, as sentences in `lang`."""
    lang = lang if lang in GO else "en"
    o = a.recommended
    values = {
        "free": a.free_units,
        "per_kw": ECON["roof_sqft_per_kw"],
        "roof": a.roof_sqft or 0,
        "known": 12 - len(a.estimated_months),
        "rate": a.export_rate,
        "load": a.sanctioned_kw,
    }
    if o:
        values.update(
            kw=o.kw,
            cover=round(o.generation_kwh / a.usage_units_per_year * 100),
            export=o.export_kwh,
        )
    reason = REASONS[a.reason][lang].format(**values)
    return reason, [NOTES[n][lang].format(**values) for n in a.notes]


def message(a: Analysis, lang: str = "en") -> str:
    lang = lang if lang in GO else "en"
    o = a.recommended
    reason, notes = explain(a, lang)

    if a.verdict == "skip":
        text = SKIP[lang].format(discom=a.discom_name, reason=reason, bill_month=_hundreds(a.bill_now_rs_per_year / 12))
    else:
        text = GO[lang].format(
            discom=a.discom_name,
            kw=o.kw,
            roof_needed=o.roof_sqft_needed,
            gross=inr(o.gross_cost),
            subsidy=inr(o.subsidy),
            net=inr(o.net_cost),
            save_low=_hundreds(o.savings_rs),
            save_high=_hundreds(max(o.savings_rs, o.savings_optimistic_rs)),
            save_month=_hundreds(o.savings_rs / 12),
            payback=o.payback_years,
            emi=inr(o.emi_rs),
            rate=o.loan_rate_pct,
            emi_after=inr(o.emi_after_subsidy_rs),
            save_25=_hundreds(o.savings_25y_rs),
            co2=o.co2_t_per_year,
            reason=reason,
        )
    return text + "".join(f"\n• {n}" for n in notes)
