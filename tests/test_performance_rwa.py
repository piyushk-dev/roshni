from datetime import datetime

from surya import bot, performance, pipeline, rwa


def test_output_check_verdicts(delhi_yield):
    oct15 = datetime(2026, 10, 15)
    expected = delhi_yield.monthly[9] * 3 * 15 / 31  # 3 kW, half of October
    ok = performance.check({"kwh_this_month": expected * 0.95}, 3, delhi_yield, oct15)
    low = performance.check({"kwh_this_month": expected * 0.8}, 3, delhi_yield, oct15)
    bad = performance.check({"kwh_today": 4.0}, 3, delhi_yield, oct15)
    assert (ok["verdict"], low["verdict"], bad["verdict"]) == ("ok", "low", "bad")
    assert performance.check({}, 3, delhi_yield, oct15) is None
    smog = performance.check({"kwh_this_month": 10}, 3, delhi_yield, datetime(2026, 12, 10))
    assert smog["smog"] and "smog" in performance.message(smog, 3, "en", assumed=False)


def test_messages_both_languages(delhi_yield):
    r = performance.check({"kwh_today": 9.0}, 3, delhi_yield, datetime(2026, 10, 15))
    for lang in ("en", "hi"):
        assert "{" not in performance.message(r, 3, lang, assumed=True)
    assert "couldn't read" in performance.message(None, 3, "en", False)


def test_rwa_message(delhi_yield):
    e = rwa.estimate(10, delhi_yield.annual)
    assert e["subsidy"] == 180000 and 2 < e["payback"] < 6
    for lang in ("en", "hi"):
        text = rwa.message(lang, delhi_yield.annual)
        assert "18,000" in text and "{" not in text


class Wa:
    def __init__(self):
        self.sent = []

    def send_text(self, to, text):
        self.sent.append(text)

    def mark_read(self, mid):
        pass

    def download_media(self, mid):
        return b"photo", "image/jpeg"


def _msg(kind, **body):
    return {"from": "whatsapp:+919800000000", "id": "m1", "type": kind, **body}


def test_inverter_photo_routes_to_the_output_check(monkeypatch, delhi_yield):
    monkeypatch.setattr(performance, "classify", lambda data, mt, client=None: "inverter_reading")
    monkeypatch.setattr(performance, "read_generation", lambda data, mt, client=None: {"kwh_today": 12.0})
    monkeypatch.setattr(pipeline, "yield_for", lambda lat, lon: delhi_yield)
    wa = Wa()
    bot.handle(_msg("image", image={"id": "i1"}), {"lang": "en"}, wa, pipeline)
    assert "SYSTEM" in wa.sent[-1]  # no size known yet
    user = bot.handle(_msg("text", text={"body": "system 3.3"}), {"lang": "en"}, wa, pipeline)
    assert user["system_kw"] == 3.3
    bot.handle(_msg("image", image={"id": "i1"}), user, wa, pipeline)
    assert "Output check · 3.3 kW" in wa.sent[-1]


def test_flat_command(monkeypatch, delhi_yield):
    monkeypatch.setattr(pipeline, "yield_for", lambda lat, lon: delhi_yield)
    wa = Wa()
    bot.handle(_msg("text", text={"body": "flat"}), {"lang": "hi"}, wa, pipeline)
    assert "सोसाइटी" in wa.sent[-1]
