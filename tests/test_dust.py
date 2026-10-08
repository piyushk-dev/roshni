from surya import handler, product
import json


def fake(pm10_by_day, dust_by_day=None):
    days = ["2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12"]
    time, pm, du = [], [], []
    for i, d in enumerate(days):
        for h in range(24):
            time.append(f"{d}T{h:02d}:00")
            pm.append(pm10_by_day[i])
            du.append((dust_by_day or [0] * 5)[i])
    return lambda url: {"hourly": {"time": time, "pm10": pm, "dust": du}}


def setup_function():
    product._dust_cache.clear()


def test_cleans_on_the_first_clear_day_after_the_dust():
    r = product.dust(28.6, 77.2, fetch=fake([200, 180, 160, 90, 80]))
    assert [d["level"] for d in r["days"]] == ["dusty", "dusty", "dusty", "clear", "clear"]
    assert r["advice"] == "clean_after" and r["clean_on"] == "2026-10-11"


def test_dust_events_count_even_when_pm10_is_moderate():
    r = product.dust(28.6, 77.2, fetch=fake([90, 90, 90, 90, 90], [0, 320, 0, 0, 0]))
    assert r["days"][1]["level"] == "high" and r["clean_on"] == "2026-10-10"


def test_all_clear_and_all_dusty_weeks():
    assert product.dust(20.0, 75.0, fetch=fake([40] * 5))["advice"] == "clear_week"
    r = product.dust(21.0, 75.0, fetch=fake([300] * 5))
    assert r["advice"] == "dusty_week" and r["clean_on"] is None


def test_results_are_cached_per_rounded_place():
    calls = []
    f = fake([50] * 5)
    product.dust(28.61, 77.21, fetch=lambda u: calls.append(u) or f(u), now=1000)
    product.dust(28.64, 77.18, fetch=lambda u: calls.append(u) or f(u), now=2000)
    assert len(calls) == 1


def test_whatsapp_message_and_bad_places():
    msg = product.dust_message(product.dust(28.6, 77.2, fetch=fake([200, 200, 90, 90, 90])), "hi")
    assert "पैनल साफ़ करें" in msg and "µg/m³" in msg
    try:
        product.dust(51.5, -0.1, fetch=fake([1] * 5))
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
