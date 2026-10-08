"""The application journey: eight stages from pre-flight check to subsidy, run by Step Functions.

One execution per household. At each stage the state machine waits on a task token; the
household replies DONE to move on. If a stage runs past its usual length the wait times out,
the household gets a nudge and, on request, a complaint drafted for whoever holds it up.
The household always sends it themselves.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

from . import load_data

J = load_data("journey.json")
STAGES = J["stages"]
DAY_S = 86400
DEMO_DAY_S = 4  # demo mode: a "day" lasts four seconds, so a 15-day stage nudges after a minute

TEXT = {
    "en": {
        "step": "📋 Step {n} of {total} · {title}",
        "owner": {
            "you": "This one is yours. Reply DONE when it's finished.",
            "vendor": "Your vendor does this, usually within {days} days. Reply DONE when it's finished.",
            "discom": "Your electricity provider does this, usually within {days} days. Reply DONE when it's finished.",
            "mnre": "The ministry pays this, usually within {days} days. Reply DONE when the money arrives.",
        },
        "commands": "Reply STUCK for a ready-to-send complaint, STATUS to see where you are.",
        "nudge": "⏰ It's been {days} days at \"{title}\", longer than the usual {usual}.",
        "start": "🚀 Your application plan has {total} steps, from a pre-flight check to the subsidy in your account. If a step takes longer than usual, you'll get a reminder here.",
        "done": "✅ Step {n} done: {title}.",
        "finish": "🎉 All {total} steps done. The subsidy should be in your account.\nNext: when your first bill after solar arrives, send it here to check the exported units were credited.",
        "status": "📍 Step {n} of {total}: {title}. {days} days so far (usually {usual}).",
        "not_started": "You haven't started an application plan yet. Reply APPLY to begin.",
        "your_step": "This step is yours, so there's no one to chase yet. What to do:",
        "wait_a_moment": "One moment, the next step is on its way.",
        "draft_head": "✉️ Here's a message to send to {to} ({how}). Fill in the parts in [brackets]:",
        "draft": "Subject: PM Surya Ghar rooftop solar application {ref}, pending at \"{title}\" for {days} days\n\nDear Sir/Madam,\n\nMy rooftop solar application under PM Surya Ghar ({ref}) has been at the \"{title}\" stage for {days} days, longer than the usual {usual} days. Please tell me what is pending and by when it will be completed.\n\nConsumer number: [your consumer number]\nApplication number: {ref}\nName: [your name]\nMobile: [your mobile]\n\nThank you.",
        "draft_next": "No reply within 7 days? Next: {next}.",
        "cta": "Reply APPLY for a step-by-step application plan with reminders.",
    },
    "hi": {
        "step": "📋 कदम {n} / {total} · {title}",
        "owner": {
            "you": "यह कदम आपका है। पूरा होने पर हो गया लिखें।",
            "vendor": "यह आपका वेंडर करता है, आम तौर पर {days} दिन में। पूरा होने पर हो गया लिखें।",
            "discom": "यह आपकी बिजली कंपनी करती है, आम तौर पर {days} दिन में। पूरा होने पर हो गया लिखें।",
            "mnre": "यह भुगतान मंत्रालय करता है, आम तौर पर {days} दिन में। पैसा आने पर हो गया लिखें।",
        },
        "commands": "शिकायत का तैयार मैसेज चाहिए तो अटका लिखें, अभी कहाँ हैं जानने के लिए स्थिति लिखें।",
        "nudge": "⏰ \"{title}\" पर {days} दिन हो गए हैं, जो आम तौर पर लगने वाले {usual} से ज़्यादा है।",
        "start": "🚀 आपके आवेदन प्लान में {total} कदम हैं, आवेदन से पहले की जाँच से लेकर खाते में सब्सिडी तक। कोई कदम ज़्यादा समय ले तो यहीं याद दिलाया जाएगा।",
        "done": "✅ कदम {n} पूरा: {title}।",
        "finish": "🎉 सभी {total} कदम पूरे। सब्सिडी आपके खाते में आ जानी चाहिए।\nआगे: सोलर के बाद का पहला बिल आए तो यहाँ भेजें, ताकि जाँचा जा सके कि ग्रिड में भेजी यूनिट जुड़ीं या नहीं।",
        "status": "📍 कदम {n} / {total}: {title}। अब तक {days} दिन (आम तौर पर {usual})।",
        "not_started": "आपने अभी आवेदन प्लान शुरू नहीं किया है। शुरू करने के लिए आवेदन लिखें।",
        "your_step": "यह कदम आपका है, इसलिए अभी किसी से शिकायत की ज़रूरत नहीं। क्या करना है:",
        "wait_a_moment": "एक पल, अगला कदम आ रहा है।",
        "draft_head": "✉️ {to} को भेजने के लिए मैसेज ({how})। [ब्रैकेट] वाली जगहें भरें:",
        "draft": "विषय: PM सूर्य घर रूफ़टॉप सोलर आवेदन {ref}, \"{title}\" पर {days} दिन से लंबित\n\nमहोदय/महोदया,\n\nPM सूर्य घर के तहत मेरा रूफ़टॉप सोलर आवेदन ({ref}) {days} दिन से \"{title}\" चरण पर है, जबकि आम तौर पर {usual} दिन लगते हैं। कृपया बताएँ कि क्या बाकी है और यह कब तक पूरा होगा।\n\nकंज़्यूमर नंबर: [आपका कंज़्यूमर नंबर]\nआवेदन नंबर: {ref}\nनाम: [आपका नाम]\nमोबाइल: [आपका मोबाइल]\n\nधन्यवाद।",
        "draft_next": "7 दिन में जवाब न आए? अगला कदम: {next}।",
        "cta": "कदम-दर-कदम आवेदन प्लान और रिमाइंडर के लिए आवेदन लिखें।",
    },
}


def _t(lang: str) -> dict:
    return TEXT[lang if lang in TEXT else "en"]


def stage_text(i: int, lang: str, days_waiting: float = 0, nudge: bool = False) -> str:
    st, t = STAGES[i], _t(lang)
    lang = lang if lang in st["title"] else "en"
    mark = "☐" if st["id"] == "check" else "•"
    lines = []
    if nudge:
        lines += [t["nudge"].format(days=round(days_waiting), title=st["title"][lang], usual=st["days"]), ""]
    lines += [t["step"].format(n=i + 1, total=len(STAGES), title=st["title"][lang]), ""]
    lines += [f"{mark} {x}" for x in st["do"][lang]]
    lines += ["", st["why"][lang], "", t["owner"][st["who"]].format(days=st["days"]), t["commands"]]
    return "\n".join(lines)


def draft(i: int, lang: str, days_waiting: float, ref: str | None = None) -> str:
    """A complaint for whoever holds this stage, escalating as the wait gets longer."""
    st, t = STAGES[i], _t(lang)
    lang = lang if lang in st["title"] else "en"
    ladder = J["escalation"][st["who"]]
    if not ladder:
        return "\n".join([t["your_step"], *[f"• {x}" for x in st["do"][lang]]])
    level = min(len(ladder) - 1, int(max(0.0, days_waiting / st["days"] - 1)))  # one rung per extra "usual" length
    to, nxt = ladder[level], ladder[min(level + 1, len(ladder) - 1)]
    letter = t["draft"].format(ref=ref or "[application number]", title=st["title"][lang], days=round(days_waiting), usual=st["days"])
    parts = [t["draft_head"].format(to=to["to"][lang], how=to["how"]), "", letter]
    if nxt is not to:
        parts += ["", t["draft_next"].format(next=f"{nxt['to'][lang]} ({nxt['how']})")]
    return "\n".join(parts)


def timeouts(seconds_per_day: int) -> list[int]:
    return [max(60, s["days"] * seconds_per_day) for s in STAGES]


def days_since(journey: dict) -> float:
    return (time.time() - journey.get("since", time.time())) / journey.get("seconds_per_day", DAY_S)


# --- talking to Step Functions --------------------------------------------------------------

def _sfn():
    import boto3

    return boto3.client("stepfunctions")


def start(wa_id: str, channel: dict, lang: str, demo: bool = False) -> dict:
    spd = DEMO_DAY_S if demo else DAY_S
    limits = timeouts(spd)
    name = f"{hashlib.sha256(wa_id.encode()).hexdigest()[:12]}-{int(time.time())}"
    run = _sfn().start_execution(
        stateMachineArn=os.environ["JOURNEY_STATE_MACHINE"], name=name,
        input=json.dumps({"wa_id": wa_id, "channel": channel, "lang": lang, "stage": 0, "nudges": 0,
                          "seconds_per_day": spd, "timeouts": limits, "timeout_s": limits[0]}),
    )
    return {"execution": run["executionArn"], "stage": 0, "since": time.time(), "seconds_per_day": spd, "demo": demo}


def advance(journey: dict) -> None:
    _sfn().send_task_success(taskToken=journey["token"], output="{}")


def task_handler(event: dict, context) -> dict:
    """Step Functions calls this to wait on a stage (with a task token) or to finish."""
    from . import store

    j = event["journey"]
    wa_id, lang = j["wa_id"], j.get("lang", "en")
    user = store.get_user(wa_id)
    journey = user.get("journey") or {}
    client = channel_client(j["channel"])
    if event["action"] == "finish":
        client.send_text(wa_id, _t(lang)["finish"].format(total=len(STAGES)))
        journey.update(done=True, token=None)
    else:
        nudge = j.get("nudges", 0) > 0
        if not nudge:
            journey["since"] = time.time()
        journey.update(token=event["token"], stage=j["stage"], seconds_per_day=j["seconds_per_day"], execution=event.get("execution"))
        client.send_text(wa_id, stage_text(j["stage"], lang, days_since(journey), nudge))
    user["journey"] = journey
    store.put_user(wa_id, user)
    return {}


class _LogOnly:
    """Dry runs: the journey runs for real, but messages only go to the logs."""

    def send_text(self, to: str, text: str) -> None:
        import logging

        logging.getLogger(__name__).warning("dry run to %s: %s", to, text.splitlines()[0])


def channel_client(channel: dict):
    if channel.get("kind") == "log":
        return _LogOnly()
    if channel.get("kind") == "twilio":
        from . import twilio_wa

        return twilio_wa.Client(channel["from"])
    from . import whatsapp

    return whatsapp
