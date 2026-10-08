"""Thin client for the WhatsApp Cloud API, plus webhook signature checks.

Secrets live in SSM Parameter Store under SSM_PREFIX: token, app-secret, verify-token.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.request
from collections.abc import Iterator

GRAPH = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION', 'v25.0')}"
_secrets: dict[str, str] = {}


def secret(name: str) -> str:
    if name not in _secrets:
        import boto3

        param = boto3.client("ssm").get_parameter(Name=f"{os.environ['SSM_PREFIX']}/{name}", WithDecryption=True)
        _secrets[name] = param["Parameter"]["Value"]
    return _secrets[name]


def valid_signature(body: bytes, header: str | None) -> bool:
    """Meta signs every webhook with the app secret; anything else is someone else posting to our URL."""
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret("app-secret").encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


def messages(payload: dict) -> Iterator[dict]:
    """Incoming messages in a webhook payload. Delivery and read receipts are skipped."""
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            yield from change.get("value", {}).get("messages", [])


def _call(url: str, payload: dict | None = None, raw: bool = False):
    headers = {"Authorization": f"Bearer {secret('token')}", "User-Agent": "surya-saathi/1.0"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=20) as r:
        body = r.read()
    return body if raw else json.loads(body)


def _send(payload: dict) -> dict:
    return _call(f"{GRAPH}/{os.environ['WA_PHONE_NUMBER_ID']}/messages", {"messaging_product": "whatsapp", **payload})


def send_text(to: str, text: str) -> dict:
    return _send({"to": to, "type": "text", "text": {"body": text[:4096]}})


def mark_read(message_id: str) -> None:
    _send({"status": "read", "message_id": message_id})


def download_media(media_id: str) -> tuple[bytes, str]:
    meta = _call(f"{GRAPH}/{media_id}")
    return _call(meta["url"], raw=True), meta["mime_type"]
