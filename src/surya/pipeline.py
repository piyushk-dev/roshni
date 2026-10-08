"""Bill photo or usage numbers -> Analysis. Shared by the HTTP API and the WhatsApp bot."""

from __future__ import annotations

import json
import os

from . import bill_reader, quote
from .calculator import Analysis, Household, analyze
from .format import BillProblem
from .solar import SolarYield, fetch_sources, solar_yield
from .tariff import Tariff

SUPPORTED_DISCOMS = ("BRPL", "BYPL", "TPDDL")
_yields: dict[str, SolarYield] = {}


def yield_for(lat: float, lon: float) -> SolarYield:
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


def _media_type(media_type: str) -> str:
    media_type = media_type.split(";")[0].strip().replace("image/jpg", "image/jpeg")
    if media_type != "application/pdf" and media_type not in bill_reader.IMAGE_FORMATS:
        raise BillProblem("file_type")
    return media_type


def check_quote(data: bytes, media_type: str, state: str = "DL") -> tuple[dict, list[quote.Flag]]:
    fields, _ = quote.read_quote(data, _media_type(media_type))
    return fields, quote.check(fields, state) if fields.get("is_solar_quote") else []


def request_from_bill(data: bytes, media_type: str) -> tuple[dict, bill_reader.BillReading]:
    """Read a bill and turn it into the same request body POST /analyze takes."""
    reading = bill_reader.read_bill(data, _media_type(media_type))
    if not reading.is_electricity_bill:
        raise BillProblem("not_a_bill")
    if reading.discom not in SUPPORTED_DISCOMS:
        raise BillProblem("unsupported_provider", provider=reading.discom_name or "another provider")
    if not reading.sanctioned_load_kw or not reading.monthly_units:
        raise BillProblem("unreadable")
    return {
        "discom": reading.discom,
        "sanctioned_kw": reading.sanctioned_load_kw,
        "monthly_units": reading.monthly_units,
        "last_bill_units": reading.units_billed,
        "last_bill_energy_rs": reading.energy_charge_rs,
    }, reading


def run(body: dict) -> Analysis:
    tariff = Tariff.for_discom(body["discom"])
    h = Household(
        discom=body["discom"],
        sanctioned_kw=float(body["sanctioned_kw"]),
        monthly_units={int(m): u for m, u in body["monthly_units"].items()},
        roof_sqft=body.get("roof_sqft"),
        last_bill_rs=body.get("last_bill_rs"),
        last_bill_units=body.get("last_bill_units"),
        last_bill_energy_rs=body.get("last_bill_energy_rs"),
    )
    lat = float(body.get("lat") or tariff.default_lat)
    lon = float(body.get("lon") or tariff.default_lon)
    return analyze(h, yield_for(lat, lon), tariff)
