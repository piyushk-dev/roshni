"""What the WhatsApp bot says back. The WhatsApp client and pipeline are passed in, so this runs in tests."""

from __future__ import annotations

import re

from . import quote
from .format import BillProblem, message

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
DEFAULT_LANG = "hi"

TEXT = {
    "welcome": {
        "en": (
            "☀️ Namaste! I'm Surya Saathi.\n\n"
            "Send a photo or PDF of your electricity bill and find out, honestly, whether rooftop solar is worth it "
            "for your home: the right size, the PM Surya Ghar subsidy, the loan EMI and the payback.\n\n"
            "📍 Share your location for sunlight at your exact address.\n"
            "Reply हिंदी for Hindi."
        ),
        "hi": (
            "☀️ नमस्ते! मैं सूर्य साथी हूँ।\n\n"
            "अपने बिजली बिल की फोटो या PDF भेजें, और जानें कि आपके घर के लिए रूफ़टॉप सोलर फ़ायदेमंद है या नहीं: "
            "सही साइज़, PM सूर्य घर सब्सिडी, लोन की EMI और कितने साल में लागत वसूल होगी।\n\n"
            "📍 अपनी लोकेशन भेजें, ताकि आपके पते की धूप से अनुमान लगे।\n"
            "Reply ENGLISH for English."
        ),
    },
    "lang_set": {"en": "Okay, replies will be in English now.", "hi": "ठीक है, अब जवाब हिंदी में आएँगे।"},
    "reading": {"en": "⏳ Reading your bill…", "hi": "⏳ आपका बिल पढ़ा जा रहा है…"},
    "location_saved": {
        "en": "📍 Got it. Estimates will use the sunlight at this spot. Now send your bill.",
        "hi": "📍 लोकेशन मिल गई। अब इसी जगह की धूप से अनुमान लगेगा। अब अपना बिल भेजें।",
    },
    "voice_soon": {
        "en": "Voice notes are coming soon. For now, send a photo of your bill.",
        "hi": "वॉइस नोट जल्द आ रहे हैं। अभी के लिए अपने बिल की फोटो भेजें।",
    },
    "deleted": {
        "en": "🗑️ Done. Everything stored about you has been deleted. Send a bill any time to start again.",
        "hi": "🗑️ हो गया। आपसे जुड़ी सारी जानकारी मिटा दी गई है। दोबारा शुरू करने के लिए कभी भी बिल भेजें।",
    },
    "error": {
        "en": "Something went wrong on our side. Please try again in a minute.",
        "hi": "हमारी तरफ़ से कुछ गड़बड़ हो गई। कृपया एक मिनट बाद फिर कोशिश करें।",
    },
}

ENGLISH_WORDS = {"english", "eng", "en"}
HINDI_WORDS = {"hindi", "हिंदी", "हिन्दी"}
DELETE_WORDS = {"delete my data", "delete", "मेरा डेटा मिटाओ"}


def handle(msg: dict, user: dict, wa, pipeline) -> dict | None:
    """Reply to one incoming message. Returns the user's updated state, or None if they asked to be forgotten."""
    to, kind = msg["from"], msg.get("type")
    wa.mark_read(msg["id"])

    if kind == "text":
        text = msg["text"]["body"].strip()
        if text.lower() in DELETE_WORDS:
            wa.send_text(to, TEXT["deleted"][user.get("lang", DEFAULT_LANG)])
            return None
        if text.lower() in ENGLISH_WORDS or text in HINDI_WORDS or text.lower() in HINDI_WORDS:
            user["lang"] = "en" if text.lower() in ENGLISH_WORDS else "hi"
            wa.send_text(to, TEXT["lang_set"][user["lang"]])
            return user
        user.setdefault("lang", "hi" if DEVANAGARI.search(text) else "en")
        wa.send_text(to, TEXT["welcome"][user["lang"]])
        return user

    lang = user.get("lang", DEFAULT_LANG)
    if kind == "location":
        user["lat"], user["lon"] = msg["location"]["latitude"], msg["location"]["longitude"]
        wa.send_text(to, TEXT["location_saved"][lang])
    elif kind in ("image", "document"):
        wa.send_text(to, TEXT["reading"][lang])
        data, media_type = wa.download_media(msg[kind]["id"])
        try:
            request, _ = pipeline.request_from_bill(data, media_type)
            a = pipeline.run({**request, **{k: user[k] for k in ("lat", "lon") if k in user}})
        except BillProblem as p:
            if p.code != "not_a_bill":
                wa.send_text(to, p.text(lang))
                return user
            q, flags, band = pipeline.check_quote(data, media_type)  # not a bill: maybe a vendor's quote
            wa.send_text(to, quote.message(q, flags, lang, band) if q.get("is_solar_quote") else p.text(lang))
            return user
        pipeline.count_analysis(a)
        wa.send_text(to, message(a, lang))
        o = a.recommended
        user["last"] = {"verdict": a.verdict, "kw": o.kw if o else None, "discom": request["discom"]}
    elif kind == "audio":
        wa.send_text(to, TEXT["voice_soon"][lang])
    else:
        wa.send_text(to, TEXT["welcome"][lang])
    return user
