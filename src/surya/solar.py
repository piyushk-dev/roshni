"""How many units one kW of panels makes in each month at a given spot.

Two independent sunlight datasets are combined, and the lower one wins each month.
PVGIS (EU JRC, ERA5 reanalysis) models a properly tilted system with losses; NASA POWER
gives satellite-measured sunlight on flat ground. ERA5 under-counts north India's winter
smog, so PVGIS alone overstates Dec-Jan output. Scaling it by NASA's lower sunlight fixes that.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

PVGIS_API = "https://re.jrc.ec.europa.eu/api/v5_3"
NASA_POWER_API = "https://power.larc.nasa.gov/api/temporal/climatology/point"
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
DAYS = (31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
SYSTEM_LOSS_PCT = 14  # PVGIS default: wiring, inverter, dust


@dataclass(frozen=True)
class SolarYield:
    """Units (kWh) per kW of panels for each month, Jan..Dec."""

    monthly: tuple[float, ...]  # conservative, the number we quote
    optimistic: tuple[float, ...]  # PVGIS alone, the top of the range
    tilt_deg: float
    azimuth_deg: float
    temp_c: tuple[float, ...] | None = None  # monthly mean air temperature, for estimating missing usage

    @property
    def annual(self) -> float:
        return sum(self.monthly)

    @property
    def annual_optimistic(self) -> float:
        return sum(self.optimistic)


def _get_json(url: str, params: dict, timeout: float = 25) -> dict:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=timeout) as r:
        return json.load(r)


def fetch_sources(lat: float, lon: float) -> dict:
    """Raw responses from all three calls, kept whole so they can be cached or used as fixtures."""
    return {
        "pvgis_pv": _get_json(f"{PVGIS_API}/PVcalc", {
            "lat": lat, "lon": lon, "peakpower": 1, "loss": SYSTEM_LOSS_PCT,
            "optimalangles": 1, "raddatabase": "PVGIS-ERA5", "outputformat": "json",
        }),
        "pvgis_horizontal": _get_json(f"{PVGIS_API}/MRcalc", {
            "lat": lat, "lon": lon, "horirrad": 1, "raddatabase": "PVGIS-ERA5", "outputformat": "json",
        }),
        "nasa_power": _get_json(NASA_POWER_API, {
            "parameters": "ALLSKY_SFC_SW_DWN,T2M", "community": "RE",
            "latitude": lat, "longitude": lon, "format": "JSON",
        }),
    }


def solar_yield(sources: dict) -> SolarYield:
    pv = sources["pvgis_pv"]
    pvgis = [0.0] * 12
    for row in pv["outputs"]["monthly"]["fixed"]:
        pvgis[row["month"] - 1] = row["E_m"]

    totals, counts = [0.0] * 12, [0] * 12
    for row in sources["pvgis_horizontal"]["outputs"]["monthly"]:
        totals[row["month"] - 1] += row["H(h)_m"]
        counts[row["month"] - 1] += 1
    era5_daily = [totals[i] / counts[i] / DAYS[i] for i in range(12)]

    params = sources["nasa_power"]["properties"]["parameter"]
    nasa = params["ALLSKY_SFC_SW_DWN"]
    temps = tuple(params["T2M"][m] for m in MONTHS) if "T2M" in params else None
    conservative = []
    for i in range(12):
        ratio = nasa[MONTHS[i]] / era5_daily[i] if nasa[MONTHS[i]] > 0 else 1.0
        conservative.append(pvgis[i] * min(1.0, ratio))

    mount = pv["inputs"]["mounting_system"]["fixed"]
    return SolarYield(tuple(conservative), tuple(pvgis), mount["slope"]["value"], mount["azimuth"]["value"], temps)
