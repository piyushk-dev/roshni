import base64
import json

import pytest

from surya import bot, handler, panel, performance

GOOD = {"is_panel_label": True, "manufacturer": "Prakash PV", "model": "PPV-545M", "pmax_w": 545, "serial": "PPV26A0912345",
        "dcr_marked": "yes", "origin": "India", "cell_origin": "India"}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.delenv("KNOWLEDGE_TABLE", raising=False)
    panel._mem_seen.clear()


def codes(flags):
    return {f["code"] for f in flags}


def test_a_dcr_indian_label_passes():
    flags = panel.check(GOOD, expect_watt=545, owner="home-a")
    assert flags == [] and panel.verdict(flags) == "ok"
    assert "fits the subsidy rules" in panel.message(GOOD, flags)


def test_imported_cells_or_module_lose_the_subsidy():
    assert codes(panel.check({**GOOD, "origin": "China", "dcr_marked": "no"}, owner="h")) >= {"imported", "dcr_missing"}
    assert "cells_imported" in codes(panel.check({**GOOD, "cell_origin": "Vietnam"}, owner="h"))
    assert panel.verdict(panel.check({**GOOD, "origin": "China"}, owner="h")) == "red"


def test_wattage_must_match_the_quote():
    assert "watt_mismatch" in codes(panel.check({**GOOD, "pmax_w": 530}, expect_watt=545, owner="h"))
    assert "watt_mismatch" not in codes(panel.check({**GOOD, "pmax_w": 548}, expect_watt=545, owner="h2"))


def test_a_serial_seen_at_another_home_is_flagged_but_not_at_the_same_home():
    assert panel.check(GOOD, owner="home-a") == []
    assert panel.check({**GOOD, "serial": "ppv26a-0912345"}, owner="home-a") == []  # same home, same serial, re-checked
    assert "serial_seen" in codes(panel.check(GOOD, owner="home-b"))


def test_samples_never_record_serials():
    panel.check(GOOD, owner="demo-1", sample=True)
    assert panel.check(GOOD, owner="real-home") == []


def test_not_a_label_and_missing_serial():
    assert codes(panel.check({"is_panel_label": False})) == {"not_label"}
    assert "serial_missing" in codes(panel.check({**GOOD, "serial": ""}, owner="h"))


def test_http_route(monkeypatch):
    monkeypatch.setattr(panel, "read_label", lambda data, media_type, client=None: ({**GOOD, "origin": "China"}, "fake"))
    event = {"requestContext": {"http": {"method": "POST"}}, "rawPath": "/panel",
             "body": json.dumps({"file_base64": base64.b64encode(b"img").decode(), "media_type": "image/png", "expect_watt": 545, "sample": True})}
    r = handler.lambda_handler(event, None)
    data = json.loads(r["body"])
    assert r["statusCode"] == 200 and data["views"]["en"]["verdict"] == "red"
    assert "Imported panels" in " ".join(data["views"]["en"]["lines"])
    assert "विदेशी पैनल" in " ".join(data["views"]["hi"]["lines"])


def test_whatsapp_routes_panel_photos(monkeypatch):
    class WA:
        def __init__(self): self.sent = []
        def mark_read(self, _): pass
        def send_text(self, _, text): self.sent.append(text)
        def download_media(self, _): return b"img", "image/jpeg"
    monkeypatch.setattr(performance, "classify", lambda data, media_type, client=None: "panel_label")
    monkeypatch.setattr(panel, "read_label", lambda data, media_type, client=None: (GOOD, "fake"))
    wa = WA()
    bot.handle({"from": "test-phone", "id": "m1", "type": "image", "image": {"id": "x"}}, {"lang": "en"}, wa, None)
    assert "Panel label" in wa.sent[-1] and "fits the subsidy rules" in wa.sent[-1]


def test_placeholder_values_from_the_model_count_as_missing():
    f = panel.clean({**GOOD, "cell_origin": "null", "origin": "Not visible", "serial": " PPV1 "})
    assert "cell_origin" not in f and "origin" not in f and f["serial"] == "PPV1"
    assert "cells_imported" not in codes(panel.check(f, owner="h"))
