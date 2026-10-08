"""WhatsApp webhook Lambdas: `webhook` verifies and acknowledges fast, `worker` does the slow part."""

from __future__ import annotations

import base64
import json
import logging
import os

from . import bot, pipeline, store, whatsapp

log = logging.getLogger()
log.setLevel(logging.INFO)


def webhook(event: dict, context) -> dict:
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

    # Meta wants a 200 within seconds and retries otherwise; reading a bill takes longer
    if any(True for _ in whatsapp.messages(json.loads(body))):
        import boto3

        boto3.client("lambda").invoke(FunctionName=os.environ["WORKER_FUNCTION"], InvocationType="Event", Payload=body)
    return {"statusCode": 200, "body": "ok"}


def worker(event: dict, context) -> None:
    for msg in whatsapp.messages(event):
        if not store.claim_message(msg["id"]):
            continue
        user = store.get_user(msg["from"])
        try:
            user = bot.handle(msg, user, whatsapp, pipeline)
        except Exception:
            log.exception("failed on message %s", msg["id"])
            whatsapp.send_text(msg["from"], bot.TEXT["error"][user.get("lang", bot.DEFAULT_LANG)])
        if user is None:
            store.delete_user(msg["from"])
        else:
            store.put_user(msg["from"], user)
