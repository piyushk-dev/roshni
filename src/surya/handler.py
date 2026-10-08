"""Lambda entry point behind API Gateway: POST /bill, POST /analyze, GET /health."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict

from . import bill_reader
from .calculator import Household, analyze
from .format import message
from .solar import SolarYield, fetch_sources, solar_yield
from .tariff import Tariff

_yields: dict[str, SolarYield] = {}


def _yield_for(lat: float, lon: float) -> SolarYield:
    """Sunlight barely changes within ~10 km, so results are cached per 0.1° cell in memory and DynamoDB."""
    lat, lon = round(lat, 1), round(lon, 1)
    key = f"{lat}:{lon}"
    if key in _yields:
        return _yields[key]

    table = None
    if os.environ.get("YIELD_TABLE"):
        import boto3

        table = boto3.resource("dynamodb").Table(os.environ["YIELD_TABLE"])
        item = table.get_item(Key={"pk": key}).get("Item")
        if item:
            _yields[key] = SolarYield(**{k: tuple(v) if isinstance(v, list) else v for k, v in json.loads(item["yield"]).items()})
            return _yields[key]

    sy = solar_yield(fetch_sources(lat, lon))
    if table:
        table.put_item(Item={"pk": key, "yield": json.dumps(sy.__dict__)})
    _yields[key] = sy
    return sy


def _household(body: dict) -> tuple[Household, Tariff, float, float]:
    tariff = Tariff.for_discom(body["discom"])
    h = Household(
        discom=body["discom"],
        sanctioned_kw=float(body["sanctioned_kw"]),
        monthly_units={int(m): u for m, u in body["monthly_units"].items()},
        roof_sqft=body.get("roof_sqft"),
        last_bill_rs=body.get("last_bill_rs"),
        last_bill_units=body.get("last_bill_units"),
    )
    return h, tariff, float(body.get("lat") or tariff.default_lat), float(body.get("lon") or tariff.default_lon)


def _response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def _from_bill(body: dict) -> tuple[dict, dict]:
    """Bill photo -> the same request body /analyze takes, plus what was read off the bill."""
    reading = bill_reader.read_bill(base64.b64decode(body["file_base64"]), body.get("media_type", "image/jpeg"))
    if not reading.is_electricity_bill:
        raise ValueError("that doesn't look like an electricity bill")
    if reading.discom not in ("BRPL", "BYPL", "TPDDL"):
        raise ValueError(f"only Delhi providers are supported so far, this bill is from {reading.discom_name or 'an unknown provider'}")
    if not reading.sanctioned_load_kw or not reading.monthly_units:
        raise ValueError("couldn't read the sanctioned load or usage history, try a clearer photo of the whole bill")
    request = {
        **{k: body[k] for k in ("lat", "lon", "roof_sqft", "lang") if k in body},
        "discom": reading.discom,
        "sanctioned_kw": reading.sanctioned_load_kw,
        "monthly_units": reading.monthly_units,
        "last_bill_rs": reading.amount_rs,
        "last_bill_units": reading.units_billed,
    }
    return request, asdict(reading)


def lambda_handler(event: dict, context) -> dict:
    route = f"{event['requestContext']['http']['method']} {event['rawPath']}"
    if route == "GET /health":
        return _response(200, {"ok": True})
    if route not in ("POST /analyze", "POST /bill"):
        return _response(404, {"error": f"no route {route}"})

    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        body = json.loads(raw)
        reading = None
        if route == "POST /bill":
            body, reading = _from_bill(body)
        h, tariff, lat, lon = _household(body)
        a = analyze(h, _yield_for(lat, lon), tariff)
    except (KeyError, ValueError, TypeError) as e:
        return _response(400, {"error": str(e)})
    result = {"analysis": a.to_dict(), "message": message(a, body.get("lang", "en"))}
    if reading:
        result["bill"] = reading
    return _response(200, result)
