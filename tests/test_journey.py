import json
from pathlib import Path

import pytest

from surya import bot, journey, store

ASL = json.loads((Path(__file__).parents[1] / "statemachine" / "journey.asl.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["en", "hi"])
def test_every_stage_renders(lang):
    for i in range(len(journey.STAGES)):
        for nudge in (False, True):
            text = journey.stage_text(i, lang, days_waiting=20, nudge=nudge)
            assert "{" not in text and journey.STAGES[i]["title"][lang] in text
        assert "{" not in journey.draft(i, lang, 40)


def test_complaints_climb_the_ladder_as_the_wait_grows():
    net_meter = next(i for i, s in enumerate(journey.STAGES) if s["id"] == "net_meter")  # usually 25 days
    assert "solar helpline" in journey.draft(net_meter, "en", 26)
    assert "nodal officer" in journey.draft(net_meter, "en", 55)
    assert "RTI" in journey.draft(net_meter, "en", 400)
    assert "This step is yours" in journey.draft(0, "en", 10)


def test_state_machine_matches_the_stage_list():
    last = ASL["States"]["Was that the last stage?"]["Choices"][0]["NumericGreaterThanEquals"]
    assert last == len(journey.STAGES) - 1
    assert len(journey.timeouts(journey.DAY_S)) == len(journey.STAGES)
    assert journey.timeouts(journey.DEMO_DAY_S)[0] == 60  # demo stages still wait at least a minute


class Wa:
    def __init__(self):
        self.sent = []

    def send_text(self, to, text):
        self.sent.append(text)

    def mark_read(self, mid):
        pass


def _text(body):
    return {"from": "whatsapp:+919800000000", "id": "m1", "type": "text", "text": {"body": body}}


def test_apply_done_stuck_status(monkeypatch):
    calls = []
    monkeypatch.setattr(journey, "start", lambda wa_id, channel, lang, demo=False: calls.append(("start", demo)) or
                        {"execution": "arn", "stage": 0, "since": 0, "seconds_per_day": 4, "demo": demo})
    monkeypatch.setattr(journey, "advance", lambda j: calls.append(("advance", j["token"])))
    wa, user = Wa(), {"lang": "en", "channel": {"kind": "twilio", "from": "whatsapp:+14155238886"}}
    user = bot.handle(_text("APPLY DEMO"), user, wa, None)
    assert calls == [("start", True)] and "8 steps" in wa.sent[-1]
    bot.handle(_text("done"), user, wa, None)
    assert "One moment" in wa.sent[-1]  # the first stage's token hasn't arrived yet
    user["journey"]["token"] = "tok-1"
    bot.handle(_text("DONE"), user, wa, None)
    assert calls[-1] == ("advance", "tok-1") and "Step 1 done" in wa.sent[-1]
    bot.handle(_text("status"), user, wa, None)
    assert "Step 1 of 8" in wa.sent[-1]
    bot.handle(_text("हो गया"), {"lang": "hi"}, wa, None)
    assert "आवेदन लिखें" in wa.sent[-1]  # Hindi, not started yet


def test_task_handler_stores_the_token_and_messages(monkeypatch):
    saved, sent = {}, []

    class Client:
        def send_text(self, to, text):
            sent.append(text)

    monkeypatch.setattr(store, "get_user", lambda wa_id: {})
    monkeypatch.setattr(store, "put_user", saved.__setitem__)
    monkeypatch.setattr(journey, "channel_client", lambda channel: Client())
    j = {"wa_id": "w1", "channel": {"kind": "twilio", "from": "x"}, "lang": "en", "stage": 3, "nudges": 1, "seconds_per_day": 4}
    journey.task_handler({"action": "wait", "token": "tok-9", "execution": "arn", "journey": j}, None)
    assert saved["w1"]["journey"]["token"] == "tok-9" and saved["w1"]["journey"]["stage"] == 3
    assert sent[0].startswith("⏰")  # a nudge, because the stage timed out once already
    journey.task_handler({"action": "finish", "journey": j}, None)
    assert "All 8 steps done" in sent[-1] and saved["w1"]["journey"]["done"]
