"""Lambda entry point behind API Gateway: POST /bill, POST /analyze, GET /health."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict
from importlib import resources

from . import knowledge, pipeline, quote
from .format import BillProblem, bonus_text, explain, message


def _response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def _fact_route(route: str) -> tuple[str, str] | None:
    parts = route.split(" ", 1)[1].strip("/").split("/")
    if route.startswith("POST ") and len(parts) == 3 and parts[0] == "facts" and parts[2] in ("confirm", "report"):
        return parts[1], parts[2]
    return None


def _fact_action(fact: tuple[str, str], event: dict) -> dict:
    fact_id, action = fact
    if fact_id not in {f["id"] for f in knowledge.facts()}:
        return _response(404, {"error": f"no fact {fact_id}"})
    if action == "confirm":
        return _response(200, knowledge.confirm(fact_id))
    body = json.loads(event.get("body") or "{}")
    if not str(body.get("value", "")).strip():
        return _response(400, {"error": "say what the new value is"})
    return _response(200, knowledge.report(fact_id, str(body["value"]), str(body.get("evidence", ""))))


def lambda_handler(event: dict, context) -> dict:
    route = f"{event['requestContext']['http']['method']} {event['rawPath']}"
    if route == "GET /health":
        return _response(200, {"ok": True})
    if route == "GET /privacy":
        page = resources.files("surya").joinpath("privacy.html").read_text(encoding="utf-8")
        return {"statusCode": 200, "headers": {"content-type": "text/html; charset=utf-8"}, "body": page}
    if route == "GET /stats":
        return _response(200, knowledge.stats())
    if route == "GET /journey":
        from .journey import J

        return _response(200, J)
    if route == "GET /facts":
        scope = (event.get("queryStringParameters") or {}).get("scope")
        return _response(200, {"facts": knowledge.facts(scope)})
    fact = _fact_route(route)
    if fact:
        return _fact_action(fact, event)
    if route not in ("POST /analyze", "POST /bill", "POST /quote"):
        return _response(404, {"error": f"no route {route}"})

    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    lang = "en"
    try:
        body = json.loads(raw)
        lang = body.get("lang", "en")
        reading = None
        if route == "POST /quote":
            q, flags, band = pipeline.check_quote(base64.b64decode(body["file_base64"]), body.get("media_type", "image/jpeg"), bool(body.get("sample")))
            if not q.get("is_solar_quote"):
                return _response(422, {"error": quote.message(q, flags, lang), "code": "not_a_quote"})
            return _response(200, {
                "quote": q,
                "flags": quote.flags_dict(flags),
                "band": band,
                "views": {code: quote.render(q, flags, code, band) for code in ("en", "hi")},
                "message": quote.message(q, flags, lang, band),
            })
        if route == "POST /bill":
            request, reading = pipeline.request_from_bill(base64.b64decode(body["file_base64"]), body.get("media_type", "image/jpeg"))
            body = {**{k: body[k] for k in ("lat", "lon", "roof_sqft") if k in body}, **request}
        a = pipeline.run(body)
        if reading:
            pipeline.count_analysis(a)
    except BillProblem as p:
        return _response(422, {"error": p.text(lang), "code": p.code})
    except (KeyError, ValueError, TypeError) as e:
        return _response(400, {"error": str(e)})
    reason, notes = explain(a, lang)
    result = {"analysis": a.to_dict(), "reason": reason, "notes": notes, "bonus": bonus_text(a, lang), "message": message(a, lang)}
    if reading:
        result["bill"] = asdict(reading)
    return _response(200, result)
