"""Place names to a state and coordinates, with Amazon Location Service.

Questions name a place ("Lucknow", "Saket, Delhi"). The scheme list needs the state, and the dust
forecast needs coordinates. Answers are cached in memory. When the service can't answer, a state's
own name or two-letter code still works, placed at the state's centre.
"""

from __future__ import annotations

import os
import re

from . import load_data
from .tariff import STATE_CENTRES

REGION = os.environ.get("AWS_REGION", "ap-south-1")
_cache: dict[str, dict | None] = {}


def _states() -> dict:
    return load_data("schemes.json")["states"]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("&", "and")).strip()


def state_in(text: str) -> str | None:
    """The state a piece of text names: a two-letter code, or a state's name anywhere in it."""
    t = (text or "").strip()
    states = _states()
    if re.fullmatch(r"[A-Za-z]{2}", t) and t.upper() in states:
        return t.upper()
    low = _norm(t)
    # longest names first, and whole words only, so "Goalpara, Assam" is Assam, not Goa
    for code, names in sorted(states.items(), key=lambda kv: -len(kv[1]["en"])):
        if re.search(r"\b" + re.escape(_norm(names["en"])) + r"\b", low) or names["hi"] in t:
            return code
    return None


def _geocode(text: str, client=None) -> dict | None:
    import boto3

    client = client or boto3.client("geo-places", region_name=REGION)
    r = client.geocode(QueryText=text[:120], Filter={"IncludeCountries": ["IND"]}, MaxResults=1, Language="en")
    items = r.get("ResultItems") or []
    if not items:
        return None
    it = items[0]
    lon, lat = it["Position"]
    region = (it.get("Address") or {}).get("Region") or {}
    code = state_in(region.get("Name", "")) or (region.get("Code") if region.get("Code") in _states() else None)
    return {"name": it.get("Title") or text, "state": code, "lat": round(lat, 4), "lon": round(lon, 4)}


def find(text: str, client=None) -> dict | None:
    """{"name", "state", "lat", "lon"} for a place in India, or None when it can't be placed."""
    key = _norm(text or "")[:120]
    if not key:
        return None
    if key in _cache:
        return _cache[key]
    try:
        place = _geocode(text, client)
    except Exception:  # an older SDK, no permission or an outage: fall back to the state's name
        place = None
    if not place or not place.get("state"):
        code = state_in(text) or (place and state_in(place["name"]))
        if code:
            found = place or {}
            lat, lon = STATE_CENTRES.get(code, (None, None))
            place = {"name": found.get("name") or _states()[code]["en"], "state": code,
                     "lat": found.get("lat", lat), "lon": found.get("lon", lon)}
    _cache[key] = place
    return place
