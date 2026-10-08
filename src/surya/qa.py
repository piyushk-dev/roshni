"""Answers a household's own questions, grounded in their estimate, their journey and the facts board."""

from __future__ import annotations

import os

import boto3

from . import bill_reader, journey, load_data

MODEL = os.environ.get("BEDROCK_TEXT_MODEL_ID", "global.amazon.nova-2-lite-v1:0")
MAX_WORDS = 90

SYSTEM = """You are Surya Saathi, a rooftop-solar helper for Indian households under the PM Surya Ghar scheme.
Answer the household's question in {language}, in at most {words} words, in plain words a first-time
buyer understands. Use only the facts below and this household's details. If the answer isn't there,
say what you don't know and point them to the PM Surya Ghar helpline 15555 or their electricity provider.
Never invent numbers, never promise a subsidy amount the facts don't support, and never ask for Aadhaar,
bank or OTP details. Plain text only, no markdown.

Facts (each with its source date):
{facts}

The 8 application steps: {steps}

This household: {household}"""


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


def answer(question: str, user: dict, lang: str, client=None) -> str:
    client = client or boto3.client("bedrock-runtime", region_name=bill_reader.REGION)
    facts = "\n".join(f"- {f['title']}: {f['value']} ({f['verified']})" for f in load_data("facts.json"))
    steps = "; ".join(f"{i + 1}. {s['title']['en']} ({s['who']}, ~{s['days']} days)" for i, s in enumerate(journey.STAGES))
    system = SYSTEM.format(language="Hindi" if lang == "hi" else "English", words=MAX_WORDS, facts=facts,
                           steps=steps, household=_household(user))
    r = client.converse(
        modelId=MODEL,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": question[:1000]}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0.2},
    )
    return "".join(c.get("text", "") for c in r["output"]["message"]["content"]).strip()
