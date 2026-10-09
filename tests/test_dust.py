import json
from datetime import datetime, timedelta, timezone

from surya import handler, product

NOW = datetime(2026, 10, 8, 6, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp()


def fake(pm10_by_day, dust_by_day=None, start="2026-10-08", last_hours=24):
    first = datetime.fromisoformat(start)
    days = [(first + timedelta(days=i)).date().isoformat() for i in range(len(pm10_by_day))]
    time, pm, du = [], [], []
    for i, d in enumerate(days):
        for h in range(24):
            time.append(f"{d}T{h:02d}:00")
            last = i == len(days) - 1
            pm.append(pm10_by_day[i] if not last or h < last_hours else None)
            du.append((dust_by_day or [0] * len(days))[i])
    return lambda url: {"hourly": {"time": time, "pm10": pm, "dust": du}}


def setup_function():
    product._dust_cache.clear()


def test_cleans_on_the_first_clear_day_after_the_dust():
    r = product.dust(28.6, 77.2, fetch=fake([200, 180, 160, 90, 80]), now=NOW)
    assert [d["level"] for d in r["days"]] == ["dusty", "dusty", "dusty", "clear", "clear"]
    assert r["advice"] == "clean_after" and r["clean_on"] == "2026-10-11"


def test_levels_follow_indias_aqi_bands_for_pm10():
    r = product.dust(28.6, 77.2, fetch=fake([100, 101, 250, 251, 60], [320, 0, 0, 0, 0]), now=NOW)
    assert [d["level"] for d in r["days"]] == ["clear", "dusty", "dusty", "high", "clear"]
    assert r["clean_on"] == "2026-10-12"


def test_a_low_day_between_dusty_ones_is_a_conditional_clean():
    r = product.dust(28.6, 77.2, fetch=fake([141, 136, 104, 92, 120]), now=NOW)
    assert r["advice"] == "clean_lull" and r["clean_on"] == "2026-10-11"
    assert "then rises again" in product.dust_message(r)


def test_all_clear_and_all_dusty_weeks():
    assert product.dust(20.0, 75.0, fetch=fake([40] * 5), now=NOW)["advice"] == "clear_week"
    r = product.dust(21.0, 75.0, fetch=fake([300] * 5), now=NOW)
    assert r["advice"] == "dusty_week" and r["clean_on"] is None


def test_results_are_cached_per_rounded_place():
    calls = []
    f = fake([50] * 5)
    product.dust(28.61, 77.21, fetch=lambda u: calls.append(u) or f(u), now=NOW)
    product.dust(28.64, 77.18, fetch=lambda u: calls.append(u) or f(u), now=NOW + 1000)
    assert len(calls) == 1


def test_the_cache_starts_a_new_day_at_midnight_in_india():
    calls = []
    f = fake([50] * 6)
    product.dust(28.6, 77.2, fetch=lambda u: calls.append(u) or f(u), now=NOW + 17.5 * 3600)  # 23:30 IST
    r = product.dust(28.6, 77.2, fetch=lambda u: calls.append(u) or f(u), now=NOW + 18.5 * 3600)  # 00:30 IST next day
    assert len(calls) == 2 and r["days"][0]["date"] == "2026-10-09"


def test_days_before_today_and_a_part_filled_last_day_are_dropped():
    # an upstream cache served after midnight starts yesterday, and its last day is mostly empty
    r = product.dust(28.6, 77.2, fetch=fake([300, 200, 180, 160, 90, 80], start="2026-10-07", last_hours=6), now=NOW)
    assert [d["date"] for d in r["days"]] == ["2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11"]
    assert r["days"][0]["pm10"] == 200
    # a fresh forecast asks for six days and keeps the first five full ones
    assert len(product.dust(19.0, 73.0, fetch=fake([50] * 6, last_hours=6), now=NOW)["days"]) == 5
    assert len(product.dust(19.1, 73.0, fetch=fake([50] * 7), now=NOW)["days"]) == 5


def test_whatsapp_message_and_bad_places():
    msg = product.dust_message(product.dust(28.6, 77.2, fetch=fake([200, 200, 90, 90, 90]), now=NOW), "hi")
    assert "पैनल साफ़ करें" in msg and "PM10 200 µg/m³" in msg
    try:
        product.dust(51.5, -0.1, fetch=fake([1] * 5), now=NOW)
    except ValueError:
        pass
    else:
        raise AssertionError("places outside India are rejected")


def test_forecast_outage_returns_502(monkeypatch):
    def boom(*a, **k):
        raise OSError("down")
    monkeypatch.setattr(product, "_fetch_json", boom)
    event = {"requestContext": {"http": {"method": "GET"}}, "rawPath": "/care/dust", "queryStringParameters": {"lat": "26.9", "lon": "75.8"}}
    r = handler.lambda_handler(event, None)
    assert r["statusCode"] == 502 and "unavailable" in json.loads(r["body"])["error"]
