"""Answers a household's own questions with the product's own tools.

A Bedrock Converse tool-use loop. The model picks the tools a question needs: the scheme list
for a state, a rough estimate from a typed bill, the scam check, the dust forecast, or this
household's application step. It answers from what they return, and every answer lists the
tools it used. Places are found with Amazon Location Service.
"""

from __future__ import annotations

import math
import os
import re
from datetime import date

import boto3

from . import bill_reader, journey, knowledge, load_data, places, product, scam
from .format import inr
from .scheme import central_subsidy

MODEL = os.environ.get("BEDROCK_TEXT_MODEL_ID", "global.amazon.nova-2-lite-v1:0")
MAX_WORDS = 80
MAX_TURNS = 4
UNITS_PER_KW_DAY = 4.0  # MNRE's rule of thumb: 1 kW of rooftop solar makes about 4 to 5 units a day
ASSUMED_RATE = 7.0  # rupees a unit, when a question gives only the bill amount

SYSTEM = """You are Surya Saathi, a rooftop-solar helper for Indian households under the PM Surya Ghar scheme.
Answer in {language}, in plain words a first-time buyer understands. Keep it short: at most {words} words
and 5 short lines, no headings. Start with the direct answer, then only the details that matter to the
question asked; leave out loans and conditions unless they ask or they change the answer.

Use the tools for every number: subsidy amounts, state top-ups, system sizes, costs, savings, dust days
and the household's own application step. Quote amounts exactly as the tools give them; never add,
multiply or work out a number yourself, and never promise a subsidy the tools or facts don't support. Pass any place the household names to the tool exactly as they wrote it.
If a place is needed and none is named, ask which state they live in. When a tool says an estimate is
rough, say so and suggest sending a photo of the electricity bill for an exact answer. If something isn't
covered, say what you don't know and point them to the PM Surya Ghar helpline 15555 or their electricity
provider. Never ask for Aadhaar, bank or OTP details. Plain text only, no markdown.

Facts (each with its source date):
{facts}

The 8 application steps: {steps}

This household: {household}"""

FALLBACK = {
    "en": "I couldn't work that out just now. The PM Surya Ghar helpline 15555 can help, or send a photo of your electricity bill.",
    "hi": "अभी मैं यह नहीं निकाल पाया। PM सूर्य घर हेल्पलाइन 15555 मदद कर सकती है, या अपने बिजली बिल की फोटो भेजें।",
}


def _spec(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"toolSpec": {"name": name, "description": description,
                         "inputSchema": {"json": {"type": "object", "properties": properties, "required": required}}}}


PLACE = {"type": "string", "description": "a state, city or locality in India, as the household wrote it"}
TOOLS = [
    _spec("schemes_for", "Government help for rooftop solar in one place: the central PM Surya Ghar subsidy for a "
          "system size, the state's own top-up if there is one, and the collateral-free loan. Use for any question "
          "about subsidy amounts, state schemes or loans.",
          {"place": PLACE, "system_kw": {"type": "number", "description": "system size in kW; 3 if not stated"}}, ["place"]),
    _spec("rough_estimate", "A rough system size, cost, subsidy, monthly saving and payback from a typed monthly bill "
          "amount or monthly units. Use when someone asks what size they need, what it costs or whether it pays.",
          {"place": PLACE, "monthly_bill_rs": {"type": "number"}, "monthly_units": {"type": "number"}}, ["place"]),
    _spec("check_offer", "Checks a solar offer, call script or forwarded message for scam signs: fees, OTP requests, "
          "look-alike portals, 'free solar', subsidy above the cap, pressure to decide today.",
          {"text": {"type": "string", "description": "the offer, in the household's words"}}, ["text"]),
    _spec("dust_forecast", "The next five days of dust and smog (PM10) for a place, and the best day to clean the panels.",
          {"place": PLACE}, ["place"]),
    _spec("application_status", "Where this household's own PM Surya Ghar application is in the 8-step plan, and how "
          "long the current step has taken against its usual time.", {}, []),
]


def _state_names(code: str) -> dict:
    return load_data("schemes.json")["states"].get(code, {"en": code, "hi": code})


def _place(text: str) -> dict:
    p = places.find(text)
    if not p or not p.get("state"):
        raise LookupError(f"couldn't place {text!r} in an Indian state; ask which state they live in")
    return p


def _card_amount(card: dict, kw: float) -> int | None:
    """What a state card pays for this size, cap included, when its rule is an amount (per kW or flat)."""
    calc = card.get("calc") or {}
    if calc.get("type") == "per_kw":
        return round(min(calc["per_kw"] * kw, calc.get("cap", math.inf)))
    if calc.get("type") == "flat":
        return round(calc["amount"])
    return None


def _state_help(cards: list[dict], kw: float) -> list[dict]:
    return [{"name": c["title"]["en"], "rule": c["amount"]["en"], "who": (c.get("who") or {}).get("en"),
             "for_this_size": inr(a) if (a := _card_amount(c, kw)) is not None else "see the rule",
             "source": c["source"]} for c in cards if c["kind"] == "state"]


def schemes_for(place: str, system_kw: float = 3) -> tuple[dict, dict]:
    p = _place(place)
    s = product.schemes(p["state"], system_kw or 3)
    cards = {c["id"]: c for c in s["schemes"]}
    state_cards = [c for c in s["schemes"] if c["kind"] == "state"]
    state_help = _state_help(state_cards, s["kw"])
    top_up = sum(_card_amount(c, s["kw"]) or 0 for c in state_cards)
    central = s["potential_central_rs"]
    out = {"state": _state_names(p["state"])["en"], "system_kw": s["kw"], "central_subsidy": inr(central),
           "central_rule": cards.get("central", {}).get("amount", {}).get("en"), "special_category_state": s["special"],
           "state_help": state_help or "no state top-up on record; the household should confirm with the state agency",
           "together_if_eligible_for_both": inr(central + top_up) if top_up else None,
           "loan_only_if_asked": cards.get("loan", {}).get("amount", {}).get("en"), "conditions": s["note"]["en"]}
    names = _state_names(p["state"])
    return out, {"en": f"the scheme list for {names['en']}", "hi": f"{names['hi']} की योजना सूची"}




def rough_estimate(place: str, monthly_bill_rs: float | None = None, monthly_units: float | None = None) -> tuple[dict, dict]:
    p = _place(place)
    state = p["state"]
    if not (monthly_units or monthly_bill_rs):
        raise ValueError("need the monthly bill amount or the monthly units")
    units = float(monthly_units or monthly_bill_rs / ASSUMED_RATE)
    rate = monthly_bill_rs / monthly_units if monthly_bill_rs and monthly_units else ASSUMED_RATE
    kw = min(10.0, max(1.0, round(units / (UNITS_PER_KW_DAY * 30) * 2) / 2))
    band = knowledge.price_band(state, kw)
    state_cards = [c for c in product.schemes(state, kw)["schemes"] if c["kind"] == "state"]
    top = sum(_card_amount(c, kw) or 0 for c in state_cards)
    cost = round(band["typical"] * kw, -3)
    central = round(central_subsidy(kw, state))
    generation = kw * UNITS_PER_KW_DAY * 30
    saving = min(generation, units) * rate
    notes = []
    if state == "DL" and units <= 200:
        notes.append("Delhi homes using up to 200 units a month already pay no energy charge, so solar may save little.")
    elif state == "DL" and units <= 400:
        notes.append("Delhi homes averaging up to 400 units a month may get up to 3 kW with nothing to pay upfront.")
    out = {"state": _state_names(state)["en"], "monthly_units": round(units),
           "units_basis": "as given" if monthly_units else f"worked back from the bill at an assumed ₹{ASSUMED_RATE:g} a unit",
           "system_kw": kw, "typical_cost": inr(cost), "central_subsidy": inr(central),
           "state_top_up_if_eligible": inr(top) if top else None,
           "state_help": _state_help(state_cards, kw) or "no state top-up on record",
           "cost_after_central_subsidy": inr(cost - central), "generation_units_per_month": round(generation),
           "saving_per_month": inr(round(saving, -1)),
           "payback_years": round((cost - central) / (saving * 12), 1) if saving else None,
           "method": "rough: 1 kW makes about 4 units a day, priced at the typical local rate per kW",
           "notes": notes, "exact_answer": "a photo of the electricity bill gives an exact estimate"}
    return out, {"en": "a rough estimate (1 kW makes about 4 units a day)", "hi": "मोटा अनुमान (1 kW रोज़ लगभग 4 यूनिट)"}


def check_offer(text: str) -> tuple[dict, dict]:
    found = scam.check(text)
    r = scam.render(found, "en")
    return {"verdict": scam.verdict(found), "summary": re.sub(r"^[^\w]+", "", r["title"]), "signs": r["signs"]}, \
        {"en": "the scam check", "hi": "धोखाधड़ी की जाँच"}


def dust_forecast(place: str) -> tuple[dict, dict]:
    p = _place(place)
    if p.get("lat") is None:
        raise LookupError(f"couldn't find coordinates for {place!r}")
    d = product.dust(p["lat"], p["lon"])
    day = date.fromisoformat(d["clean_on"]).strftime("%A %d %B") if d["clean_on"] else ""
    advice = product.DUST_TEXT["en"][d["advice"]].format(day=day)
    out = {"place": p["name"], "days": [{"date": x["date"], "level": x["level"], "pm10": x["pm10"]} for x in d["days"]],
           "advice": re.sub(r"^[^\w]+", "", advice), "clean_on": d["clean_on"]}
    return out, {"en": f"the dust forecast for {p['name'].split(',')[0]}", "hi": f"{p['name'].split(',')[0]} का धूल अनुमान"}


def application_status(user: dict) -> tuple[dict, dict]:
    j = user.get("journey") or {}
    label = {"en": "your application's step", "hi": "आपके आवेदन का कदम"}
    if not j:
        return {"started": False, "how_to_start": "reply APPLY on WhatsApp to start the 8-step plan"}, label
    if j.get("done"):
        return {"started": True, "done": True}, label
    st = journey.STAGES[j.get("stage", 0)]
    return {"started": True, "step": j.get("stage", 0) + 1, "of": len(journey.STAGES), "title": st["title"]["en"],
            "who_acts": st["who"], "usual_days": st["days"], "days_so_far": round(journey.days_since(j), 1)}, label


def run_tool(name: str, args: dict, user: dict) -> tuple[dict, dict | None]:
    """A tool's result for the model, and a label for the "worked out with" line (None when it failed)."""
    try:
        if name == "schemes_for":
            return schemes_for(str(args.get("place", "")), float(args.get("system_kw") or 3))
        if name == "rough_estimate":
            num = lambda k: float(args[k]) if args.get(k) not in (None, "", 0) else None
            return rough_estimate(str(args.get("place", "")), num("monthly_bill_rs"), num("monthly_units"))
        if name == "check_offer":
            return check_offer(str(args.get("text", "")))
        if name == "dust_forecast":
            return dust_forecast(str(args.get("place", "")))
        if name == "application_status":
            return application_status(user)
        return {"error": f"no tool called {name}"}, None
    except (LookupError, ValueError, TypeError) as e:
        return {"error": str(e)}, None
    except Exception:  # an outside service failed; the model can still answer without it
        return {"error": "that tool isn't available right now"}, None


def _household(user: dict) -> str:
    parts = []
    last = user.get("last") or {}
    if last:
        parts.append(f"last estimate: {last.get('verdict')}, {last.get('kw')} kW recommended, provider {last.get('discom')}")
    j = user.get("journey") or {}
    if j and not j.get("done"):
        st = journey.STAGES[j.get("stage", 0)]
        parts.append(f"application at step {j.get('stage', 0) + 1}: {st['title']['en']}")
    return "; ".join(parts) or "no bill sent yet"


def _clean(text: str) -> str:
    # Nova can think aloud in <thinking> tags around tool calls; the household sees only the answer
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.S)
    text = re.sub(r"</?thinking>", "", text)
    return text.replace("**", "").strip()


def answer_full(question: str, user: dict, lang: str, client=None) -> dict:
    """{"text": the answer, "used": labels of the tools that fed it}."""
    client = client or boto3.client("bedrock-runtime", region_name=bill_reader.REGION)
    facts = "\n".join(f"- {f['title']}: {f['value']} ({f['verified']})" for f in load_data("facts.json"))
    steps = "; ".join(f"{i + 1}. {s['title']['en']} ({s['who']}, ~{s['days']} days)" for i, s in enumerate(journey.STAGES))
    system = SYSTEM.format(language="Hindi" if lang == "hi" else "English", words=MAX_WORDS, facts=facts,
                           steps=steps, household=_household(user))
    messages = [{"role": "user", "content": [{"text": question[:1000]}]}]
    used: list[dict] = []
    for _ in range(MAX_TURNS):
        r = client.converse(modelId=MODEL, system=[{"text": system}], messages=messages,
                            toolConfig={"tools": TOOLS, "toolChoice": {"auto": {}}},
                            inferenceConfig={"maxTokens": 700, "temperature": 0.2})
        msg = r["output"]["message"]
        calls = [c["toolUse"] for c in msg["content"] if "toolUse" in c]
        if not calls:
            text = _clean("".join(c.get("text", "") for c in msg["content"]))
            return {"text": text or FALLBACK.get(lang, FALLBACK["en"]), "used": used}
        messages.append(msg)
        results = []
        for call in calls:
            out, label = run_tool(call["name"], call.get("input") or {}, user)
            if label and label not in used:
                used.append(label)
            results.append({"toolResult": {"toolUseId": call["toolUseId"], "content": [{"json": out}],
                                           **({"status": "error"} if "error" in out else {})}})
        messages.append({"role": "user", "content": results})
    return {"text": FALLBACK.get(lang, FALLBACK["en"]), "used": used}


def answer(question: str, user: dict, lang: str, client=None) -> str:
    return answer_full(question, user, lang, client)["text"]
