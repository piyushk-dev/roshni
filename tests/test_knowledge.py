import json

from surya import handler, knowledge
from surya.tariff import Tariff


def test_without_a_table_everything_falls_back_to_seeds(monkeypatch):
    monkeypatch.delenv("KNOWLEDGE_TABLE", raising=False)
    band = knowledge.price_band("DL", 3)
    assert band["live"] is False and band["typical"] == 65000
    facts = knowledge.facts("DL")
    assert {f["scope"] for f in facts} == {"IN", "DL"}
    assert all(f["status"] == "current" for f in facts)
    knowledge.record_price("DL", 3, 60000)  # no-op, must not raise
    assert knowledge.stats() == {}


def test_live_band_needs_enough_quotes(monkeypatch):
    prices = [{"kw": 3, "per_kw": p} for p in (52000, 56000, 58000, 60000, 61000, 64000, 70000, 90000)]
    monkeypatch.setattr(knowledge, "_recent", lambda pk, days, limit=100: prices)
    band = knowledge.price_band("DL", 3)
    assert band["live"] and band["quotes"] == 8 and band["low"] < band["typical"] < band["high"]
    monkeypatch.setattr(knowledge, "_recent", lambda pk, days, limit=100: prices[:3])
    assert knowledge.price_band("DL", 3)["live"] is False


def test_reports_flag_a_fact(monkeypatch):
    state = {}
    monkeypatch.setattr(knowledge, "_fact_state", lambda fid: json.loads(json.dumps(state.get(fid, {}))))
    monkeypatch.setattr(knowledge, "_save_fact_state", lambda fid, st: state.__setitem__(fid, st))
    for _ in range(knowledge.REPORTS_TO_FLAG):
        knowledge.report("dl-fppas", "BRPL 19.1%", "photo of my October bill")
    knowledge.confirm("helpline")
    by_id = {f["id"]: f for f in knowledge.facts("DL")}
    assert by_id["dl-fppas"]["status"] == "reported_changed" and by_id["dl-fppas"]["report_count"] == 3
    assert by_id["helpline"]["confirmations"] == 1


def test_watcher_marks_facts_whose_page_changed(monkeypatch):
    state = {}
    monkeypatch.setattr(knowledge, "_fact_state", lambda fid: dict(state.get(fid, {})))
    monkeypatch.setattr(knowledge, "_save_fact_state", lambda fid, st: state.__setitem__(fid, st))
    assert knowledge.watch(fetch=lambda url: b"<p>version one</p>") == []  # first look just records
    changed = knowledge.watch(fetch=lambda url: b"<p>version two</p>")
    assert changed and all(state[i]["status"] == "source_changed" for i in changed)


def test_learned_tariff_from_spec():
    t = Tariff.from_spec({"state": "UP", "provider": "UPPCL", "slabs": [[150, 5.5], [300, 6.0], [None, 6.5]], "fixed_per_kw": 110})
    assert t.learned and t.state == "UP" and t.default_lat > 26
    assert t.energy_charge(200) == 150 * 5.5 + 50 * 6.0
    assert t.fixed_charge(3) == 330


def _event(method, path, body=None, query=None):
    return {"requestContext": {"http": {"method": method}}, "rawPath": path, "queryStringParameters": query,
            "body": json.dumps(body) if body is not None else None}


def test_fact_and_stats_routes(monkeypatch):
    monkeypatch.setattr(knowledge, "_fact_state", lambda fid: {})
    monkeypatch.setattr(knowledge, "_save_fact_state", lambda fid, st: None)
    assert handler.lambda_handler(_event("GET", "/stats"), None)["statusCode"] == 200
    facts = json.loads(handler.lambda_handler(_event("GET", "/facts", query={"scope": "DL"}), None)["body"])["facts"]
    assert any(f["id"] == "dl-zero-upfront" for f in facts)
    assert handler.lambda_handler(_event("POST", "/facts/helpline/confirm"), None)["statusCode"] == 200
    assert handler.lambda_handler(_event("POST", "/facts/nope/confirm"), None)["statusCode"] == 404
    assert handler.lambda_handler(_event("POST", "/facts/helpline/report", {"value": ""}), None)["statusCode"] == 400
    assert handler.lambda_handler(_event("POST", "/facts/helpline/report", {"value": "1800-180-3333"}), None)["statusCode"] == 200
