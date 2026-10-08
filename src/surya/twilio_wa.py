"""WhatsApp through the Twilio Sandbox, for when a Meta business account can't be verified.

Speaks the same small interface as `whatsapp` (send_text, mark_read, download_media), and turns
Twilio's form-encoded webhooks into the Meta-shaped messages `bot.handle` already understands.
Secrets live next to Meta's in SSM: twilio-account-sid, twilio-auth-token.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from .whatsapp import secret

API = "https://api.twilio.com/2010-04-01"
MAX_BODY = 1600  # Twilio's limit for one WhatsApp message
log = logging.getLogger(__name__)


def valid_signature(url: str, params: dict[str, str], header: str | None) -> bool:
    """Twilio signs the full URL plus every POST field, sorted by name, with the auth token."""
    if not header:
        return False
    payload = url + "".join(k + params[k] for k in sorted(params))
    digest = hmac.new(secret("twilio-auth-token").encode(), payload.encode(), hashlib.sha1).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode(), header)


def to_message(params: dict[str, str]) -> dict:
    """A Twilio webhook as the Meta-style message dict `bot.handle` takes."""
    msg = {"from": params["From"], "id": params["MessageSid"]}
    media_type = params.get("MediaContentType0", "")
    if int(params.get("NumMedia") or 0) > 0:
        kind = "image" if media_type.startswith("image/") else "audio" if media_type.startswith("audio/") else "document"
        msg.update(type=kind, **{kind: {"id": params["MediaUrl0"], "mime_type": media_type}})
    elif params.get("Latitude") and params.get("Longitude"):
        msg.update(type="location", location={"latitude": float(params["Latitude"]), "longitude": float(params["Longitude"])})
    else:
        msg.update(type="text", text={"body": params.get("Body", "")})
    return msg


def chunks(text: str, size: int = MAX_BODY) -> list[str]:
    """Split on line breaks so no WhatsApp message goes over Twilio's limit."""
    out, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > size and current:
            out.append(current)
            current = ""
        current = f"{current}\n{line}" if current else line
    return [*out, current] if current else out


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    """Replies from the sandbox number the user wrote to."""

    def __init__(self, from_number: str):
        self.from_number = from_number

    def _auth(self) -> str:
        pair = f"{secret('twilio-account-sid')}:{secret('twilio-auth-token')}"
        return "Basic " + base64.b64encode(pair.encode()).decode()

    def send_text(self, to: str, text: str) -> None:
        url = f"{API}/Accounts/{secret('twilio-account-sid')}/Messages.json"
        for part in chunks(text):
            data = urllib.parse.urlencode({"From": self.from_number, "To": to, "Body": part}).encode()
            req = urllib.request.Request(url, data=data, headers={"Authorization": self._auth()})
            with urllib.request.urlopen(req, timeout=20) as r:
                log.info("sent %s", json.load(r).get("sid"))

    def send_media(self, to: str, media_url: str, text: str = "") -> None:
        url = f"{API}/Accounts/{secret('twilio-account-sid')}/Messages.json"
        data = urllib.parse.urlencode({"From": self.from_number, "To": to, "MediaUrl": media_url, **({"Body": text} if text else {})}).encode()
        req = urllib.request.Request(url, data=data, headers={"Authorization": self._auth()})
        with urllib.request.urlopen(req, timeout=20) as r:
            log.info("sent media %s", json.load(r).get("sid"))

    def mark_read(self, message_id: str) -> None:
        """Twilio's sandbox has no read receipts."""

    def download_media(self, media_url: str) -> tuple[bytes, str]:
        # Twilio answers with a redirect to signed storage; that host rejects our Basic auth header
        req = urllib.request.Request(media_url, headers={"Authorization": self._auth()})
        try:
            r = urllib.request.build_opener(_NoRedirect).open(req, timeout=20)
        except urllib.error.HTTPError as e:
            if e.code not in (301, 302, 303, 307, 308):
                raise
            r = urllib.request.urlopen(e.headers["Location"], timeout=20)
        with r:
            return r.read(), r.headers.get_content_type()
