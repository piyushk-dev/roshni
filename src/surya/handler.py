"""Lambda entry point behind API Gateway: POST /bill, POST /analyze, GET /health."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict
from importlib import resources

from . import pipeline
from .format import message


def _response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def lambda_handler(event: dict, context) -> dict:
    route = f"{event['requestContext']['http']['method']} {event['rawPath']}"
    if route == "GET /health":
        return _response(200, {"ok": True})
    if route == "GET /privacy":
        page = resources.files("surya").joinpath("privacy.html").read_text(encoding="utf-8")
        return {"statusCode": 200, "headers": {"content-type": "text/html; charset=utf-8"}, "body": page}
    if route not in ("POST /analyze", "POST /bill"):
        return _response(404, {"error": f"no route {route}"})

    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        body = json.loads(raw)
        reading = None
        if route == "POST /bill":
            request, reading = pipeline.request_from_bill(base64.b64decode(body["file_base64"]), body.get("media_type", "image/jpeg"))
            body = {**{k: body[k] for k in ("lat", "lon", "roof_sqft", "lang") if k in body}, **request}
        a = pipeline.run(body)
    except (KeyError, ValueError, TypeError) as e:
        return _response(400, {"error": str(e)})
    result = {"analysis": a.to_dict(), "message": message(a, body.get("lang", "en"))}
    if reading:
        result["bill"] = asdict(reading)
    return _response(200, result)
