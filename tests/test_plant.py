import json
from datetime import date, datetime, timedelta

import pytest

from surya import handler, plant

IST = plant.IST


def weather(start="2026-09-10", days=35, ghi_noon=800, rain=None):
    """Clear days: sunlight a smooth hump from 06:00 to 18:00."""
    first = date.fromisoformat(start)
    hours, daily = {"time": [], "shortwave_radiation": [], "temperature_2m": [], "precipitation": []}, \
        {"time": [], "sunrise": [], "sunset": [], "weather_code": [], "temperature_2m_max": [], "precipitation_sum": []}
    for i in range(days):
        d = (first + timedelta(days=i)).isoformat()
        for h in range(24):
            hours["time"].append(f"{d}T{h:02d}:00")
            x = (h - 0.5 - 12) / 6
            hours["shortwave_radiation"].append(max(0.0, ghi_noon * (1 - x * x)))
            hours["temperature_2m"].append(30.0)
            hours["precipitation"].append(0.0)
        daily["time"].append(d); daily["sunrise"].append(f"{d}T06:00"); daily["sunset"].append(f"{d}T18:00")
        daily["weather_code"].append(0); daily["temperature_2m_max"].append(33.0)
        daily["precipitation_sum"].append((rain or {}).get(d, 0.0))
    return lambda url: {"hourly": hours, "daily": daily}


NOON = datetime(2026, 10, 11, 12, 0, tzinfo=IST).timestamp()
NIGHT = datetime(2026, 10, 11, 21, 0, tzinfo=IST).timestamp()
DUST = {"days": [], "advice": "clear_week", "clean_on": None}


@pytest.fixture(autouse=True)
def fresh():
    plant._cache.clear()


def test_power_follows_sunlight_heat_and_dust():
    assert plant.power_kw(3, 0, 30, 0) == 0
    clean, dusty = plant.power_kw(3, 800, 30, 0), plant.power_kw(3, 800, 30, 0.1)
    assert 1.8 < clean < 2.4 and dusty == pytest.approx(clean * 0.9)
    assert plant.power_kw(3, 800, 45, 0) < clean          # hot cells make less
    assert plant.power_kw(3, 2000, 10, 0) == 3            # capped at the inverter


def test_a_clear_day_in_numbers():
    r = plant.simulate(3, 28.6, 77.2, cleaned="2026-10-01", fetch=weather(), dust=DUST, now=NOON)
    assert r["simulated"] and r["now"]["status"] in ("producing", "overvoltage", "undervoltage", "outage", "offline")
    t = r["today"]
    assert 12 < t["clean_kwh"] < 18 and t["day_kwh"] <= t["clean_kwh"]
    assert 0 < t["soiling_pct"] <= 15 and t["dust_loss_rs"] >= 0
    assert t["self_used_kwh"] + t["exported_kwh"] == pytest.approx(t["so_far_kwh"], abs=0.3)
    assert len(r["ahead"]) == 3 and all(a["kwh"] > 0 for a in r["ahead"])
    assert r["lifetime"]["co2_t"] > 0 and r["years"][-1]["share"] == pytest.approx(0.88)


def test_night_is_asleep_and_rain_washes_the_panels():
    r = plant.simulate(3, 28.6, 77.2, cleaned="2026-09-01", fetch=weather(rain={"2026-10-10": 8.0}), dust=DUST, now=NIGHT)
    assert r["now"]["status"] == "night" and r["now"]["power_kw"] == 0
    assert r["today"]["soiling_pct"] < 1   # yesterday's rain washed off a month of dust


def test_events_are_explained_and_stable():
    a = plant.simulate(3, 28.6, 77.2, fetch=weather(), dust=DUST, now=NIGHT)
    plant._cache.clear()
    b = plant.simulate(3, 28.6, 77.2, fetch=weather(), dust=DUST, now=NIGHT)
    assert a["events"] == b["events"]  # the same home and day always tell the same story
    for e in a["events"]:
        assert e["title"] and e["todo"] and a["device"]["serial"] in e["evidence"]


def test_promise_check_and_route(monkeypatch):
    r = plant.simulate(3, 28.6, 77.2, promised=360, fetch=weather(), dust=DUST, now=NOON)
    assert r["month"]["on_track_pct"] == round(r["month"]["projected_kwh"] / 360 * 100)
    monkeypatch.setattr(plant, "simulate", lambda *a, **k: {"ok": a[:2]})
    event = {"requestContext": {"http": {"method": "GET"}}, "rawPath": "/plant", "queryStringParameters": {"kw": "4"}}
    assert json.loads(handler.lambda_handler(event, None)["body"]) == {"ok": ["4", 28.61]}
