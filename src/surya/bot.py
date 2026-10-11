"""What the WhatsApp bot says back. The WhatsApp client and pipeline are passed in, so this runs in tests."""

from __future__ import annotations

import re

from . import doctor, journey, market, panel, performance, product, qa, quote, rwa, scam, voice
from .format import BillProblem, message

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
DEFAULT_LANG = "hi"

TEXT = {
    "welcome": {
        "en": (
            "☀️ Namaste! I'm Surya Saathi, your rooftop-solar helper.\n\n"
            "Send a photo or PDF of your electricity bill to find out, honestly, whether solar is worth it for your "
            "home: the right size, the PM Surya Ghar subsidy, the EMI and the payback.\n\n"
            "You can also:\n"
            "• ask anything, typed or as a voice note\n"
            "• send a vendor's quote or a panel's label to check it\n"
            "• reply QUOTES to compare vendors, SCAM with an offer you got, SCHEMES UP for a state's help, DUST for the day to clean\n"
            "• share your location for sunlight at your address\n\n"
            "Reply हिंदी for Hindi."
        ),
        "hi": (
            "☀️ नमस्ते! मैं सूर्य साथी हूँ, आपका रूफ़टॉप सोलर साथी।\n\n"
            "अपने बिजली बिल की फोटो या PDF भेजें और जानें कि आपके घर के लिए सोलर फ़ायदेमंद है या नहीं: "
            "सही साइज़, PM सूर्य घर सब्सिडी, EMI और कितने साल में लागत वसूल होगी।\n\n"
            "आप यह भी कर सकते हैं:\n"
            "• कुछ भी पूछें, लिखकर या वॉइस नोट से\n"
            "• वेंडर का कोटेशन या पैनल का लेबल जाँच के लिए भेजें\n"
            "• वेंडरों की तुलना के लिए QUOTES, मिले ऑफ़र के साथ SCAM, राज्य की मदद के लिए SCHEMES UP, सफ़ाई के दिन के लिए DUST लिखें\n"
            "• अपने पते की धूप के अनुमान के लिए लोकेशन भेजें\n\n"
            "Reply ENGLISH for English."
        ),
    },
    "lang_set": {"en": "Okay, replies will be in English now.", "hi": "ठीक है, अब जवाब हिंदी में आएँगे।"},
    "reading": {"en": "⏳ Reading your photo…", "hi": "⏳ आपकी फोटो पढ़ी जा रही है…"},
    "system_set": {"en": "Got it: a {kw:g} kW system. Send a photo of your inverter or solar app any time to check its output.",
                   "hi": "ठीक है: {kw:g} kW सिस्टम। उत्पादन जाँचने के लिए कभी भी इन्वर्टर या सोलर ऐप की फोटो भेजें।"},
    "need_size": {"en": "What size is your system? Reply SYSTEM followed by its kW, for example SYSTEM 3.",
                  "hi": "आपका सिस्टम कितने kW का है? SYSTEM और फिर kW लिखें, जैसे SYSTEM 3।"},
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
FLAT_WORDS = {"flat", "apartment", "society", "rwa", "फ्लैट", "फ़्लैट", "सोसाइटी"}
SYSTEM_SIZE = re.compile(r"^system\s+(\d+(?:\.\d+)?)\s*(?:kw)?$", re.IGNORECASE)
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
    if not j.get("demo"):  # demo days last seconds; they would distort the real timings
        from . import knowledge

        provider = (user.get("last") or {}).get("provider") or (user.get("last") or {}).get("discom") or "unknown"
        knowledge.record_stage(provider, journey.STAGES[j["stage"]]["id"], journey.days_since(j))
    journey.advance(j)
    st = journey.STAGES[j["stage"]]
    j["token"] = None
    return t["done"].format(n=j["stage"] + 1, title=st["title"].get(lang, st["title"]["en"]))


def _output_check(data: bytes, media_type: str, user: dict, wa, to: str, lang: str, pipeline) -> dict:
    reading = performance.read_generation(data, media_type)
    kw = reading.get("system_kw") or user.get("system_kw") or (user.get("last") or {}).get("kw")
    if not kw:
        wa.send_text(to, TEXT["need_size"][lang])
        return user
    assumed = not reading.get("system_kw") and not user.get("system_kw")
    sy = pipeline.yield_for(user.get("lat") or 28.61, user.get("lon") or 77.21)
    wa.send_text(to, performance.message(performance.check(reading, kw, sy), kw, lang, assumed))
    return user


def handle(msg: dict, user: dict, wa, pipeline) -> dict | None:
    """Reply to one incoming message. Returns the user's updated state, or None if they asked to be forgotten."""
    to, kind = msg["from"], msg.get("type")
    wa.mark_read(msg["id"])

    if kind == "text":
        text = msg["text"]["body"].strip()
        if text.lower() in DELETE_WORDS:
            market.forget_user(to)
            wa.send_text(to, TEXT["deleted"][user.get("lang", DEFAULT_LANG)])
            return None
        if text.lower() in ENGLISH_WORDS or text in HINDI_WORDS or text.lower() in HINDI_WORDS:
            user["lang"] = "en" if text.lower() in ENGLISH_WORDS else "hi"
            wa.send_text(to, TEXT["lang_set"][user["lang"]])
            return user
        user.setdefault("lang", "hi" if DEVANAGARI.search(text) else "en")
        lang = user["lang"]
        low = text.lower().strip()
        if low in ("quotes", "कोटेशन") or (user.get("asking_pin") and re.fullmatch(r"[1-9]\d{5}", text)):
            last = user.get("last") or {}
            if not last.get("kw"):
                wa.send_text(to, market.TEXT[lang]["no_request"])
                return user
            if re.fullmatch(r"[1-9]\d{5}", text):
                state = last.get("state", "DL")
                view = market.create_request({"kw": last["kw"], "state": state, "discom": last.get("discom", ""), "pincode": text, "source": "whatsapp"}, wa_id=to)
                user["market_request"] = view["request"]["id"]
                user.pop("asking_pin", None)
                wa.send_text(to, market.wa_started(view, lang))
            elif user.get("market_request"):
                try:
                    wa.send_text(to, market.wa_compare(market.view(user["market_request"]), lang))
                except KeyError:
                    user.pop("market_request", None)
                    user["asking_pin"] = True
                    wa.send_text(to, market.TEXT[lang]["ask_pin"])
            else:
                user["asking_pin"] = True
                wa.send_text(to, market.TEXT[lang]["ask_pin"])
            return user
        if low.startswith("choose"):
            try:
                view = market.view(user["market_request"])
                if not view["quotes"]:
                    wa.send_text(to, market.TEXT[lang]["no_quotes_yet"])
                    return user
                match = re.fullmatch(r"choose\s+([1-9]\d*)", low)
                if not match or int(match[1]) > len(view["quotes"]):
                    raise ValueError("bad choice")
                chosen = market.choose(view["request"]["id"], view["quotes"][int(match[1])-1]["vendor_id"])
                wa.send_text(to, market.wa_chosen(chosen, lang))
            except (KeyError, ValueError):
                wa.send_text(to, market.TEXT[lang]["bad_choice"])
            return user
        if low.startswith("scam ") or low.startswith("check offer ") or scam.looks_like_offer(text):
            wa.send_text(to, scam.message(text, lang))
            return user
        if low in ("my solar", "solar", "plant", "panels", "मेरा सोलर", "सोलर", "पैनल"):
            from . import plant
            last = user.get("last") or {}
            try:
                said = "hi" if DEVANAGARI.search(text) else lang  # a Hindi command gets a Hindi answer
                r = plant.simulate(user.get("system_kw") or last.get("kw") or 3, user.get("lat") or 28.61, user.get("lon") or 77.21, lang=said)
                wa.send_text(to, plant.message(r, said))
            except Exception:
                wa.send_text(to, "The panels' data isn't available right now. Try again in a while." if lang == "en" else "पैनल का डेटा अभी नहीं मिल रहा। थोड़ी देर बाद फिर कोशिश करें।")
            return user
        if low in ("dust", "clean", "cleaning", "धूल", "सफ़ाई", "सफाई"):
            try:
                wa.send_text(to, product.dust_message(product.dust(user.get("lat"), user.get("lon")), lang))
            except Exception:
                wa.send_text(to, "Dust forecast unavailable right now. Try again in a while." if lang == "en" else "धूल का अनुमान अभी नहीं मिल रहा। थोड़ी देर बाद फिर कोशिश करें।")
            return user
        if low in ("passport", "handover", "checklist", "पासपोर्ट"):
            groups = product.checklists()["groups"]
            wa.send_text(to, "\n\n".join(g["title"][lang]+"\n"+"\n".join("☐ "+i["text"][lang] for i in g["items"]) for g in groups))
            return user
        if low == "schemes" or low.startswith("schemes "):
            try:
                code = low.split()[1].upper() if len(low.split()) > 1 else (user.get("last") or {}).get("state", "DL")
                catalog = product.schemes(code, (user.get("last") or {}).get("kw") or 3)
                wa.send_text(to, "\n\n".join(s["title"][lang]+"\n"+s["amount"][lang]+"\n"+s["source"] for s in catalog["schemes"] if s["kind"] in ("central", "state")))
            except ValueError:
                wa.send_text(to, "Use SCHEMES and a state code, for example SCHEMES UP or SCHEMES AS.")
            return user
        cmd = _command(text)
        if cmd:
            wa.send_text(to, journey_reply(cmd, text, user, to, user["lang"]))
            return user
        size = SYSTEM_SIZE.match(text.strip())
        if size:
            user["system_kw"] = float(size.group(1))
            wa.send_text(to, TEXT["system_set"][user["lang"]].format(kw=user["system_kw"]))
            return user
        if text.lower().strip(" !.") in FLAT_WORDS:
            sy = pipeline.yield_for(user.get("lat") or 28.61, user.get("lon") or 77.21)
            wa.send_text(to, rwa.message(user["lang"], sy.annual))
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
        doc = performance.classify(data, media_type)
        if doc == "solar_quote":
            q, flags, band = pipeline.check_quote(data, media_type)
            wa.send_text(to, quote.message(q, flags, lang, band))
            return user
        if doc == "inverter_reading":
            return _output_check(data, media_type, user, wa, to, lang, pipeline)
        if doc == "panel_label":
            fields, _ = panel.read_label(data, media_type)
            wa.send_text(to, panel.message(fields, panel.check(fields, owner=to), lang))
            return user
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
        user["last"] = {"verdict": a.verdict, "kw": o.kw if o else None, "discom": request["discom"], "provider": a.discom_name,
                        "state": reading.state or "DL"}
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
