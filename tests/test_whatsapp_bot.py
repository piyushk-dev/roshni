import hashlib
import hmac
import json

import pytest
from test_bill_reader import FIELDS, FakeBedrock

from surya import bill_reader, bot, pipeline, wa_handler, whatsapp


class FakeWhatsApp:
    def __init__(self):
        self.sent, self.read = [], []

    def send_text(self, to, text):
        self.sent.append(text)

    def mark_read(self, message_id):
        self.read.append(message_id)

    def download_media(self, media_id):
        return b"photo", "image/jpeg"


@pytest.fixture
def wa(monkeypatch, delhi_yield):
    monkeypatch.setattr(pipeline, "yield_for", lambda lat, lon: delhi_yield)
    real = bill_reader.read_bill
    monkeypatch.setattr(bill_reader, "read_bill", lambda data, mt: real(data, mt, client=FakeBedrock()))
    return FakeWhatsApp()


def _msg(kind, **body):
    return {"from": "919800000000", "id": f"wamid.{kind}", "type": kind, **body}


def test_first_text_gets_a_welcome_in_the_script_used(wa):
    user = bot.handle(_msg("text", text={"body": "नमस्ते"}), {}, wa, pipeline)
    assert user["lang"] == "hi" and "रोशनी" in wa.sent[-1]
    user = bot.handle(_msg("text", text={"body": "hello"}), {}, wa, pipeline)
    assert user["lang"] == "en" and "Roshni" in wa.sent[-1]
    assert wa.read == ["wamid.text", "wamid.text"]


def test_language_can_be_switched(wa):
    user = bot.handle(_msg("text", text={"body": "ENGLISH"}), {"lang": "hi"}, wa, pipeline)
    assert user["lang"] == "en"
    user = bot.handle(_msg("text", text={"body": "हिंदी"}), user, wa, pipeline)
    assert user["lang"] == "hi"


def test_bill_photo_gets_an_estimate_in_hindi_by_default(wa):
    user = bot.handle(_msg("image", image={"id": "media1"}), {}, wa, pipeline)
    assert wa.sent[0].startswith("⏳")
    assert "सही साइज़" in wa.sent[1]
    assert user["last"]["verdict"] == "go"


def test_location_is_used_for_the_next_bill(wa, monkeypatch, delhi_yield):
    seen = []
    monkeypatch.setattr(pipeline, "yield_for", lambda lat, lon: seen.append((lat, lon)) or delhi_yield)
    user = bot.handle(_msg("location", location={"latitude": 28.7, "longitude": 77.1}), {"lang": "en"}, wa, pipeline)
    bot.handle(_msg("image", image={"id": "media1"}), user, wa, pipeline)
    assert seen == [(28.7, 77.1)]


def test_bill_from_elsewhere_gets_a_clear_answer(wa, monkeypatch):
    other = {**FIELDS, "discom": "OTHER", "discom_name": "UPPCL"}
    monkeypatch.setattr(FakeBedrock, "converse", lambda self, modelId, **r: {"output": {"message": {"content": [{"toolUse": {"input": dict(other)}}]}}})
    bot.handle(_msg("image", image={"id": "media1"}), {"lang": "en"}, wa, pipeline)
    assert "UPPCL" in wa.sent[-1] and "charges table" in wa.sent[-1]  # no rates on the bill to learn from


def test_bill_from_elsewhere_with_rates_is_answered_from_its_own_tariff(wa, monkeypatch):
    other = {**FIELDS, "discom": "OTHER", "discom_name": "UPPCL", "state": "UP",
             "slab_rows": [{"units": 100, "rate": 5.5}, {"units": 50, "rate": 5.5}, {"units": 150, "rate": 6.0}, {"units": 262, "rate": 6.5}],
             "fixed_charge_rs": 600}
    monkeypatch.setattr(FakeBedrock, "converse", lambda self, modelId, **r: {"output": {"message": {"content": [{"toolUse": {"input": dict(other)}}]}}})
    bot.handle(_msg("image", image={"id": "media1"}), {"lang": "en"}, wa, pipeline)
    estimate = next(m for m in wa.sent if "Solar estimate" in m)
    assert "UPPCL" in estimate and "rates printed on your bill" in estimate
    assert "APPLY" in wa.sent[-1]  # a "go" answer offers the application plan


def test_signature_check(monkeypatch):
    monkeypatch.setattr(whatsapp, "secret", lambda name: "s3cret")
    body = b'{"entry":[]}'
    good = "sha256=" + hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
    assert whatsapp.valid_signature(body, good)
    assert not whatsapp.valid_signature(body, "sha256=" + "0" * 64)
    assert not whatsapp.valid_signature(body, None)


def test_webhook_verifies_and_hands_off(monkeypatch):
    secrets = {"verify-token": "vt", "app-secret": "s3cret"}
    monkeypatch.setattr(whatsapp, "secret", secrets.__getitem__)
    monkeypatch.setenv("WORKER_FUNCTION", "worker")
    invoked = []

    class FakeLambda:
        def invoke(self, **kw):
            invoked.append(kw)

    import boto3

    monkeypatch.setattr(boto3, "client", lambda name: FakeLambda())

    get = {"requestContext": {"http": {"method": "GET"}}, "queryStringParameters": {"hub.mode": "subscribe", "hub.verify_token": "vt", "hub.challenge": "42"}}
    assert wa_handler.webhook(get, None)["body"] == "42"
    get["queryStringParameters"]["hub.verify_token"] = "wrong"
    assert wa_handler.webhook(get, None)["statusCode"] == 403

    payload = json.dumps({"entry": [{"changes": [{"value": {"messages": [_msg("text", text={"body": "hi"})]}}]}]})
    sig = "sha256=" + hmac.new(b"s3cret", payload.encode(), hashlib.sha256).hexdigest()
    post = {"requestContext": {"http": {"method": "POST"}}, "headers": {"X-Hub-Signature-256": sig}, "body": payload}
    assert wa_handler.webhook(post, None)["statusCode"] == 200
    assert invoked and invoked[0]["InvocationType"] == "Event"

    receipts = json.dumps({"entry": [{"changes": [{"value": {"statuses": [{"status": "read"}]}}]}]})
    sig = "sha256=" + hmac.new(b"s3cret", receipts.encode(), hashlib.sha256).hexdigest()
    wa_handler.webhook({**post, "body": receipts, "headers": {"x-hub-signature-256": sig}}, None)
    assert len(invoked) == 1  # read receipts don't wake the worker

    post["headers"]["X-Hub-Signature-256"] = "sha256=bad"
    assert wa_handler.webhook(post, None)["statusCode"] == 401


def test_delete_my_data_forgets_the_user(wa):
    assert bot.handle(_msg("text", text={"body": "DELETE MY DATA"}), {"lang": "en", "lat": 28.6}, wa, pipeline) is None
    assert "deleted" in wa.sent[-1]


def test_privacy_page_is_served():
    from surya import handler

    out = handler.lambda_handler({"requestContext": {"http": {"method": "GET"}}, "rawPath": "/privacy"}, None)
    assert out["statusCode"] == 200 and "text/html" in out["headers"]["content-type"]
    assert "DELETE MY DATA" in out["body"]


def test_secret_is_fetched_on_first_use_even_right_after_boot(monkeypatch):
    """Regression: a fresh Lambda's monotonic clock can start near 0, which once skipped the first fetch."""
    import boto3

    class FakeSSM:
        def get_parameter(self, Name, WithDecryption):
            return {"Parameter": {"Value": f"value-of-{Name}"}}

    monkeypatch.setattr(whatsapp, "_secrets", {})
    monkeypatch.setattr(whatsapp.time, "monotonic", lambda: 1.0)
    monkeypatch.setenv("SSM_PREFIX", "/p")
    monkeypatch.setattr(boto3, "client", lambda name: FakeSSM())
    assert whatsapp.secret("app-secret") == "value-of-/p/app-secret"
