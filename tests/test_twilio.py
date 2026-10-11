import base64
import hashlib
import hmac
import urllib.parse

import pytest

from surya import store, twilio_wa, wa_handler, whatsapp

URL = "https://api.example.com/twilio"
PARAMS = {"MessageSid": "SM1", "From": "whatsapp:+919800000000", "To": "whatsapp:+14155238886", "Body": "hi", "NumMedia": "0"}


def sign(params, url=URL, token="tok"):
    payload = url + "".join(k + params[k] for k in sorted(params))
    return base64.b64encode(hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()).decode()


@pytest.fixture(autouse=True)
def secrets(monkeypatch):
    monkeypatch.setattr(whatsapp, "secret", {"twilio-auth-token": "tok", "twilio-account-sid": "AC1"}.__getitem__)
    monkeypatch.setattr(twilio_wa, "secret", {"twilio-auth-token": "tok", "twilio-account-sid": "AC1"}.__getitem__)


def test_signature():
    assert twilio_wa.valid_signature(URL, PARAMS, sign(PARAMS))
    assert not twilio_wa.valid_signature(URL, {**PARAMS, "Body": "tampered"}, sign(PARAMS))
    assert not twilio_wa.valid_signature(URL, PARAMS, None)


@pytest.mark.parametrize("extra, kind", [
    ({"NumMedia": "1", "MediaContentType0": "image/jpeg", "MediaUrl0": "https://m/1"}, "image"),
    ({"NumMedia": "1", "MediaContentType0": "application/pdf", "MediaUrl0": "https://m/2"}, "document"),
    ({"NumMedia": "1", "MediaContentType0": "audio/ogg", "MediaUrl0": "https://m/3"}, "audio"),
    ({"Latitude": "28.6", "Longitude": "77.2"}, "location"),
    ({}, "text"),
])
def test_messages_take_the_meta_shape(extra, kind):
    msg = twilio_wa.to_message({**PARAMS, **extra})
    assert msg["type"] == kind and msg["from"] == PARAMS["From"] and msg["id"] == "SM1"
    if kind in ("image", "document", "audio"):
        assert msg[kind]["id"] == extra["MediaUrl0"]


def test_long_replies_are_split_on_lines():
    text = "\n".join(f"line {i} " + "x" * 90 for i in range(40))
    parts = twilio_wa.chunks(text)
    assert len(parts) > 1 and all(len(p) <= twilio_wa.MAX_BODY for p in parts)
    assert "\n".join(parts) == text


def _event(params, signature):
    return {
        "rawPath": "/twilio",
        "requestContext": {"http": {"method": "POST"}},
        "headers": {"Host": "api.example.com", "X-Twilio-Signature": signature},
        "isBase64Encoded": True,
        "body": base64.b64encode(urllib.parse.urlencode(params).encode()).decode(),
    }


def test_webhook_acknowledges_and_hands_off(monkeypatch):
    handed = []
    monkeypatch.setattr(wa_handler, "_hand_off", handed.append)
    out = wa_handler.webhook(_event(PARAMS, sign(PARAMS)), None)
    assert out["statusCode"] == 200 and out["body"] == "<Response/>"
    assert handed == [{"channel": "twilio", "params": PARAMS}]
    assert wa_handler.webhook(_event(PARAMS, "bad"), None)["statusCode"] == 401


def test_worker_replies_through_twilio(monkeypatch):
    sent, saved = [], {}
    monkeypatch.setattr(store, "claim_message", lambda mid: True)
    monkeypatch.setattr(store, "get_user", lambda wa_id: {})
    monkeypatch.setattr(store, "put_user", saved.__setitem__)
    monkeypatch.setattr(twilio_wa.Client, "send_text", lambda self, to, text: sent.append((self.from_number, to, text)))
    wa_handler.worker({"channel": "twilio", "params": PARAMS}, None)
    assert sent[0][0] == "whatsapp:+14155238886" and sent[0][1] == PARAMS["From"]
    assert "Roshni" in sent[0][2]
    assert saved[PARAMS["From"]]["lang"] == "en"
