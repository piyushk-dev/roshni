from surya import bot, qa, voice


class Wa:
    def __init__(self):
        self.sent, self.media = [], []

    def send_text(self, to, text):
        self.sent.append(text)

    def send_media(self, to, url, text=""):
        self.media.append(url)

    def mark_read(self, mid):
        pass

    def download_media(self, mid):
        return b"OggS...", "audio/ogg"


def _msg(kind, **body):
    return {"from": "whatsapp:+919800000000", "id": "m1", "type": kind, **body}


def test_typed_questions_get_answers_and_greetings_get_the_welcome(monkeypatch):
    asked = []
    monkeypatch.setattr(qa, "answer", lambda q, user, lang: asked.append((q, lang)) or "Yes, up to ₹2 lakh without collateral.")
    wa = Wa()
    bot.handle(_msg("text", text={"body": "hello"}), {}, wa, None)
    assert "Roshni" in wa.sent[-1] and not asked
    bot.handle(_msg("text", text={"body": "Can I get a loan for solar?"}), {"lang": "en"}, wa, None)
    assert asked == [("Can I get a loan for solar?", "en")] and "collateral" in wa.sent[-1]
    bot.handle(_msg("text", text={"body": "क्या लोन मिलेगा?"}), {"lang": "en"}, wa, None)
    assert asked[-1][1] == "hi"  # a Hindi question is answered in Hindi


def test_voice_note_in_voice_note_out(monkeypatch):
    monkeypatch.setattr(voice, "transcribe", lambda data, mt: ("सब्सिडी कब आएगी", "hi"))
    monkeypatch.setattr(voice, "speak", lambda text, lang: "https://example/answer.mp3")
    monkeypatch.setattr(qa, "answer", lambda q, user, lang: "ई-टोकन रिडीम करने के 15–30 दिन बाद।")
    wa = Wa()
    user = bot.handle(_msg("audio", audio={"id": "a1"}), {}, wa, None)
    assert wa.sent[0].startswith("🎙️") and "सब्सिडी" in wa.sent[0]
    assert "ई-टोकन" in wa.sent[1] and wa.media == ["https://example/answer.mp3"]
    assert user["lang"] == "hi"


def test_spoken_commands_drive_the_journey(monkeypatch):
    monkeypatch.setattr(voice, "transcribe", lambda data, mt: ("status", "en"))
    monkeypatch.setattr(voice, "speak", lambda text, lang: "https://example/a.mp3")
    wa = Wa()
    bot.handle(_msg("audio", audio={"id": "a1"}), {"lang": "en"}, wa, None)
    assert "haven't started" in wa.sent[1]


def test_unclear_voice_note(monkeypatch):
    monkeypatch.setattr(voice, "transcribe", lambda data, mt: ("  ", "hi"))
    wa = Wa()
    bot.handle(_msg("audio", audio={"id": "a1"}), {"lang": "en"}, wa, None)
    assert "didn't come through" in wa.sent[-1] and not wa.media


def test_answers_are_grounded_in_the_household():
    seen = {}

    class Fake:
        def converse(self, **kw):
            seen.update(kw)
            return {"output": {"message": {"content": [{"text": " Ask your provider. "}]}}}

    user = {"last": {"verdict": "go", "kw": 2, "discom": "BRPL"}, "journey": {"stage": 5}}
    assert qa.answer("When will the net meter come?", user, "en", client=Fake()) == "Ask your provider."
    system = seen["system"][0]["text"]
    assert "2 kW recommended" in system and "step 6: Net meter and inspection" in system and "15555" in system


def test_ask_route(monkeypatch):
    import json

    from surya import handler

    monkeypatch.setattr(qa, "answer_full", lambda q, user, lang: {"text": f"[{lang}] {q} {user.get('last', {}).get('kw')}", "used": []})
    ev = lambda body: {"requestContext": {"http": {"method": "POST"}}, "rawPath": "/ask", "body": json.dumps(body)}
    out = json.loads(handler.lambda_handler(ev({"question": "Loan?", "lang": "hi", "last": {"kw": 2}}), None)["body"])
    assert out["answer"] == "[hi] Loan? 2"
    assert handler.lambda_handler(ev({"question": "  "}), None)["statusCode"] == 400


def test_voice_replies_drop_emoji_markers_and_links_and_spell_units():
    said = voice.speakable("🔴 For 3 kW:\n- Central: ₹78,000\n• See https://pmsuryaghar.gov.in\nPM10 141 µg/m³ ✅", "en")
    assert "🔴" not in said and "✅" not in said and "https" not in said and not said.startswith("-")
    assert "3 kilowatt" in said and "₹78,000" in said and "micrograms" in said
    assert "किलोवाट" in voice.speakable("3 kW पर ₹78,000", "hi")
