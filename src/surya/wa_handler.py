"""WhatsApp webhook Lambdas: `webhook` verifies and acknowledges fast, `worker` does the slow part.

Two ways in: /whatsapp from Meta's Cloud API and /twilio from the Twilio Sandbox. Both end up
in the same `bot.handle`.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.parse

from . import bot, pipeline, store, twilio_wa, whatsapp

log = logging.getLogger()
log.setLevel(logging.INFO)


def _hand_off(payload: dict) -> None:
    import boto3

    boto3.client("lambda").invoke(FunctionName=os.environ["WORKER_FUNCTION"], InvocationType="Event", Payload=json.dumps(payload))


def _twilio_webhook(event: dict) -> dict:
    raw = event.get("body") or ""
    form = base64.b64decode(raw).decode("utf-8") if event.get("isBase64Encoded") else raw
    params = dict(urllib.parse.parse_qsl(form, keep_blank_values=True))
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if not twilio_wa.valid_signature(f"https://{headers.get('host')}{event['rawPath']}", params, headers.get("x-twilio-signature")):
        log.warning("rejected a Twilio webhook with a bad signature")
        return {"statusCode": 401, "body": "bad signature"}
    if params.get("MessageSid"):
        _hand_off({"channel": "twilio", "params": params})
    return {"statusCode": 200, "headers": {"content-type": "text/xml"}, "body": "<Response/>"}


def webhook(event: dict, context) -> dict:
    if event.get("rawPath") == "/twilio":
        return _twilio_webhook(event)
    if event["requestContext"]["http"]["method"] == "GET":
        q = event.get("queryStringParameters") or {}
        if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == whatsapp.secret("verify-token"):
            return {"statusCode": 200, "headers": {"content-type": "text/plain"}, "body": q.get("hub.challenge", "")}
        return {"statusCode": 403, "body": "forbidden"}

    raw = event.get("body") or ""
    body = base64.b64decode(raw) if event.get("isBase64Encoded") else raw.encode("utf-8")
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if not whatsapp.valid_signature(body, headers.get("x-hub-signature-256")):
        log.warning("rejected a webhook with a bad signature")
        return {"statusCode": 401, "body": "bad signature"}

    payload = json.loads(body)
    for s in whatsapp.statuses(payload):
        errors = [f"{e.get('code')} {e.get('title')}: {e.get('error_data', {}).get('details', '')}" for e in s.get("errors", [])]
        log.log(logging.WARNING if errors else logging.INFO, "delivery %s for %s %s", s.get("status"), s.get("id"), "; ".join(errors))

    # Meta wants a 200 within seconds and retries otherwise; reading a bill takes longer
    if any(True for _ in whatsapp.messages(payload)):
        _hand_off(payload)
    return {"statusCode": 200, "body": "ok"}


def worker(event: dict, context) -> None:
    if event.get("channel") == "twilio":
        msgs, client = [twilio_wa.to_message(event["params"])], twilio_wa.Client(event["params"]["To"])
        channel = {"kind": "twilio", "from": event["params"]["To"]}
    else:
        msgs, client, channel = list(whatsapp.messages(event)), whatsapp, {"kind": "meta"}
    for msg in msgs:
        if not store.claim_message(msg["id"]):
            continue
        user = store.get_user(msg["from"])
        user["channel"] = channel  # so journey reminders go back the way the household came in
        try:
            user = bot.handle(msg, user, client, pipeline)
        except Exception:
            log.exception("failed on message %s", msg["id"])
            client.send_text(msg["from"], bot.TEXT["error"][user.get("lang", bot.DEFAULT_LANG)])
        if user is None:
            store.delete_user(msg["from"])
        else:
            store.put_user(msg["from"], user)
