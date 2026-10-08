"""For households without a roof of their own: solar on the housing society's common areas."""

from __future__ import annotations

from .format import inr
from .scheme import SCHEME

PER_KW_SUBSIDY = 18000  # PM Surya Ghar, common facilities of a group housing society / RWA
MAX_KW = 500
COMMON_AREA_RATE = 7.5  # ₹ per unit a society typically pays for lifts, pumps and lights (estimate)
EXAMPLE_KW = 10


def estimate(kw: float, yield_per_kw: float) -> dict:
    gross = kw * SCHEME["cost_rs_per_kw"]["above_3kw"]["typical"]
    subsidy = min(kw, MAX_KW) * PER_KW_SUBSIDY
    saves = kw * yield_per_kw * COMMON_AREA_RATE
    return {"kw": kw, "gross": gross, "subsidy": subsidy, "net": gross - subsidy, "saves": saves, "payback": (gross - subsidy) / saves}


TEXT = {
    "en": (
        "🏢 Live in a flat? Your society can go solar for its common areas.\n\n"
        "• PM Surya Ghar pays ₹18,000 per kW for a housing society's common facilities (lifts, water pumps, lights, EV charging), up to 500 kW.\n"
        "• A {kw:g} kW system costs about {gross} before subsidy, gets {subsidy} back, and cuts the common-area bill by roughly {saves} a year: it pays for itself in about {payback:.1f} years.\n"
        "• Some states, Delhi among them, also allow virtual or group net metering, so one system can credit every participating flat's bill.\n\n"
        "Forward this to your RWA:\n\n"
        "\"Dear Committee, PM Surya Ghar gives our society ₹18,000 per kW for rooftop solar on common areas, up to 500 kW. "
        "A {kw:g} kW system would cost about {net} after subsidy and could cut our common-area electricity bill by about {saves} a year. "
        "Can we discuss this at the next meeting and invite two registered vendors to quote?\""
    ),
    "hi": (
        "🏢 फ़्लैट में रहते हैं? आपकी सोसाइटी अपने कॉमन एरिया के लिए सोलर लगा सकती है।\n\n"
        "• PM सूर्य घर हाउसिंग सोसाइटी की कॉमन सुविधाओं (लिफ़्ट, पानी के पंप, लाइटें, EV चार्जिंग) के लिए ₹18,000 प्रति kW देता है, 500 kW तक।\n"
        "• {kw:g} kW सिस्टम सब्सिडी से पहले लगभग {gross} का है, {subsidy} वापस मिलते हैं, और कॉमन एरिया का बिल सालाना लगभग {saves} घटता है: लगभग {payback:.1f} साल में लागत वसूल।\n"
        "• कुछ राज्यों में, जिनमें दिल्ली भी है, वर्चुअल या ग्रुप नेट मीटरिंग की सुविधा है, जिससे एक सिस्टम से हर जुड़े फ़्लैट के बिल में क्रेडिट मिल सकता है।\n\n"
        "यह अपनी RWA को भेजें:\n\n"
        "\"माननीय समिति, PM सूर्य घर योजना में हमारी सोसाइटी को कॉमन एरिया पर रूफ़टॉप सोलर के लिए ₹18,000 प्रति kW मिलते हैं, 500 kW तक। "
        "{kw:g} kW सिस्टम सब्सिडी के बाद लगभग {net} का पड़ेगा और हमारे कॉमन एरिया के बिजली बिल में सालाना लगभग {saves} की बचत कर सकता है। "
        "क्या अगली बैठक में इस पर चर्चा करके दो रजिस्टर्ड वेंडर से कोटेशन मँगवा सकते हैं?\""
    ),
}


def message(lang: str, yield_per_kw: float) -> str:
    e = estimate(EXAMPLE_KW, yield_per_kw)
    return TEXT[lang if lang in TEXT else "en"].format(kw=e["kw"], gross=inr(round(e["gross"], -4)), subsidy=inr(e["subsidy"]),
                                                        net=inr(round(e["net"], -4)), saves=inr(round(e["saves"], -3)), payback=e["payback"])
