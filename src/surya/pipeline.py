"""Bill photo or usage numbers -> Analysis. Shared by the HTTP API and the WhatsApp bot."""

from __future__ import annotations

import json
import os

from . import bill_reader, knowledge, quote
from .calculator import Analysis, Household, analyze
from .format import BillProblem
from .solar import SolarYield, fetch_sources, solar_yield
from .tariff import Tariff

SUPPORTED_DISCOMS = ("BRPL", "BYPL", "TPDDL")
_yields: dict[str, SolarYield] = {}


def yield_for(lat: float, lon: float) -> SolarYield:
    """Sunlight barely changes within ~10 km, so results are cached per 0.1° cell in memory and DynamoDB."""
    lat, lon = round(lat, 1), round(lon, 1)
    key = f"v2:{lat}:{lon}"  # v2 added monthly temperature
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


def check_quote(data: bytes, media_type: str, sample: bool = False) -> tuple[dict, list[quote.Flag], dict]:
    fields, _ = quote.read_quote(data, _media_type(media_type))
    if not fields.get("is_solar_quote"):
        return fields, [], {}
    state = (fields.get("state") or "DL").upper()[:2]
    band = knowledge.price_band(state, fields.get("system_kw") or 3)
    flags = quote.check(fields, state, band)
    if not sample:  # the bundled sample quote must not move live prices or counters
        total, kw = fields.get("total_price_rs"), fields.get("system_kw")
        if total and kw:
            gst = 1 + quote.GST_ON_SYSTEMS if fields.get("gst_included") == "no" else 1
            knowledge.record_price(state, kw, total * gst / kw)
        knowledge.count(quotes_checked=1, red_flags=sum(f.level == "red" for f in flags))
    return fields, flags, band


def _learned_tariff(reading: bill_reader.BillReading) -> dict | None:
    """The bill's own rates, or the last rates another bill from the same provider taught us."""
    state, provider = (reading.state or "IN"), (reading.discom_name or "your provider")
    if reading.slabs:
        fixed_per_kw = reading.fixed_charge_rs / reading.sanctioned_load_kw if reading.fixed_charge_rs and reading.sanctioned_load_kw else None
        return {"state": state, "provider": provider, "slabs": reading.slabs, "fixed_per_kw": fixed_per_kw, "from": "this bill"}
    seen = knowledge.learned_tariff(state, provider)
    if seen:
        return {"state": state, "provider": provider, "slabs": seen["slabs"], "fixed_per_kw": seen.get("fixed_per_kw"),
                "from": f"{seen['bills']} earlier bills"}
    return None


def request_from_bill(data: bytes, media_type: str) -> tuple[dict, bill_reader.BillReading]:
    """Read a bill and turn it into the same request body POST /analyze takes."""
    reading = bill_reader.read_bill(data, _media_type(media_type))
    if not reading.is_electricity_bill:
        raise BillProblem("not_a_bill")
    if not reading.sanctioned_load_kw or not reading.monthly_units:
        raise BillProblem("unreadable")
    request = {
        "discom": reading.discom,
        "sanctioned_kw": reading.sanctioned_load_kw,
        "monthly_units": reading.monthly_units,
        "last_bill_units": reading.units_billed,
        "last_bill_energy_rs": reading.energy_charge_rs,
    }
    if reading.slabs:  # every bill teaches its provider's current tariff
        fixed_per_kw = reading.fixed_charge_rs / reading.sanctioned_load_kw if reading.fixed_charge_rs else None
        knowledge.record_tariff(reading.state or "IN", reading.discom_name or reading.discom, reading.slabs, fixed_per_kw, None, reading.billing_month)
    if reading.discom not in SUPPORTED_DISCOMS:
        learned = _learned_tariff(reading)
        if not learned:
            raise BillProblem("unsupported_provider", provider=reading.discom_name or "your provider")
        request["tariff"] = learned
    return request, reading


def count_analysis(a) -> None:
    o = a.recommended
    knowledge.count(bills_read=1, homes_go=1 if a.verdict == "go" else 0, kw_recommended=o.kw if o else 0,
                    co2_t_per_year=o.co2_t_per_year if o else 0)


def tariff_for(body: dict) -> Tariff:
    return Tariff.from_spec(body["tariff"]) if body.get("tariff") else Tariff.for_discom(body["discom"])


def bill_checkup(reading: bill_reader.BillReading, body: dict) -> list:
    from . import doctor

    found = doctor.check(reading, tariff_for(body))
    knowledge.count(bill_savings_rs=sum(f.saves_rs for f in found))
    return found


def run(body: dict) -> Analysis:
    tariff = tariff_for(body)
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
