"""What the WhatsApp bot says back. The WhatsApp client and pipeline are passed in, so this runs in tests."""

from __future__ import annotations

import re

from . import doctor, journey, qa, quote, voice
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
    "heard": {"en": "🎙️ You said: “{text}”", "hi": "🎙️ आपने कहा: “{text}”"},
    "not_heard": {
        "en": "Sorry, that voice note didn't come through clearly. Try again a little closer to the phone, or type your question.",
        "hi": "वॉइस नोट साफ़ समझ नहीं आया। फ़ोन के थोड़ा पास से फिर कोशिश करें, या सवाल लिखकर भेजें।",
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
GREETINGS = {"hi", "hii", "hello", "hey", "namaste", "namaskar", "नमस्ते", "नमस्कार", "menu", "start over"}
COMMANDS = {
    "apply": {"apply", "start", "apply demo", "आवेदन", "aavedan"},
    "done": {"done", "हो गया", "ho gaya", "हो गया है"},
    "stuck": {"stuck", "help", "अटका", "अटक गया", "atka"},
    "status": {"status", "स्थिति", "sthiti"},
}


def _command(text: str) -> str | None:
    low = text.lower().strip(" .!")
    return next((name for name, words in COMMANDS.items() if low in words), None)


def journey_reply(cmd: str, text: str, user: dict, to: str, lang: str) -> str:
    """APPLY starts the Step Functions journey; DONE moves it on; STUCK drafts a complaint; STATUS says where."""
    t = journey.TEXT[lang if lang in journey.TEXT else "en"]
    j = user.get("journey")
    active = j and not j.get("done")
    if cmd == "apply":
        if active:
            return journey.stage_text(j["stage"], lang)
        user["journey"] = journey.start(to, user.get("channel", {}), lang, demo="demo" in text.lower())
        return t["start"].format(total=len(journey.STAGES))
    if not active:
        return t["not_started"]
    if cmd == "status":
        st = journey.STAGES[j["stage"]]
        return t["status"].format(n=j["stage"] + 1, total=len(journey.STAGES), title=st["title"].get(lang, st["title"]["en"]),
                                  days=round(journey.days_since(j)), usual=st["days"])
    if cmd == "stuck":
        return journey.draft(j["stage"], lang, max(journey.days_since(j), journey.STAGES[j["stage"]]["days"] * 1.2))
    if not j.get("token"):
        return t["wait_a_moment"]
    journey.advance(j)
    st = journey.STAGES[j["stage"]]
    j["token"] = None
    return t["done"].format(n=j["stage"] + 1, title=st["title"].get(lang, st["title"]["en"]))


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
        cmd = _command(text)
        if cmd:
            wa.send_text(to, journey_reply(cmd, text, user, to, user["lang"]))
            return user
        if text.lower().strip(" !.") in GREETINGS or len(text) < 4:
            wa.send_text(to, TEXT["welcome"][user["lang"]])
            return user
        wa.send_text(to, qa.answer(text, user, "hi" if DEVANAGARI.search(text) else user["lang"]))
        return user

    lang = user.get("lang", DEFAULT_LANG)
    if kind == "location":
        user["lat"], user["lon"] = msg["location"]["latitude"], msg["location"]["longitude"]
        wa.send_text(to, TEXT["location_saved"][lang])
    elif kind in ("image", "document"):
        wa.send_text(to, TEXT["reading"][lang])
        data, media_type = wa.download_media(msg[kind]["id"])
        try:
            request, reading = pipeline.request_from_bill(data, media_type)
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
        checkup = doctor.message(pipeline.bill_checkup(reading, request), lang)
        if checkup:
            wa.send_text(to, checkup)
        if a.verdict == "go" and not (user.get("journey") and not user["journey"].get("done")):
            wa.send_text(to, journey.TEXT[lang if lang in journey.TEXT else "en"]["cta"])
        o = a.recommended
        user["last"] = {"verdict": a.verdict, "kw": o.kw if o else None, "discom": request["discom"]}
    elif kind == "audio":
        data, media_type = wa.download_media(msg["audio"]["id"])
        text, heard_lang = voice.transcribe(data, media_type)
        if not text.strip():
            wa.send_text(to, TEXT["not_heard"][lang])
            return user
        user.setdefault("lang", heard_lang)
        wa.send_text(to, TEXT["heard"][heard_lang].format(text=text))
        cmd = _command(text)
        reply = journey_reply(cmd, text, user, to, heard_lang) if cmd else qa.answer(text, user, heard_lang)
        wa.send_text(to, reply)
        if hasattr(wa, "send_media"):  # answer a voice note with a voice note
            wa.send_media(to, voice.speak(reply, heard_lang))
    else:
        wa.send_text(to, TEXT["welcome"][lang])
    return user
