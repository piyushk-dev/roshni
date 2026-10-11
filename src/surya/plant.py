"""A simulated inverter cloud: what a home's panels did this month, are doing now, and will do next.

Real monitoring needs each brand's cloud (Growatt, Sungrow, Solis and others) and the installer's access,
so the demo runs a simulator in its place, labelled as one everywhere. It isn't random. Power follows the
sunlight, temperature and rain Open-Meteo reports for the home's own location, past month and next three
days, less the dust gathering since the panels were last cleaned (faster on dusty days, washed off by
rain). Days can also carry the inverter events owners report most: grid voltage too high at midday,
supply voltage too low, a power cut, the Wi-Fi logger dropping out. Each comes with what it means and
what to do, because the usual answer from installers is that someone else is to blame.
"""

from __future__ import annotations

import hashlib
import time
from datetime import date, datetime, timedelta, timezone

from . import product

IST = timezone(timedelta(hours=5, minutes=30))
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_S = 1800
_cache: dict[tuple, tuple[float, dict]] = {}

TILT_GAIN = 1.08         # a south-facing tilt catches a little more than flat ground
SYSTEM_LOSS = 0.86       # wiring, mismatch and the inverter
TEMP_COEFF = -0.0037     # per degree of cell temperature above 25 °C
SOIL_PER_DAY = 0.0025    # output lost to dust each dry day, before the day's dust level
SOIL_CAP = 0.15
DUST_PACE = {"clear": 1.0, "dusty": 1.6, "high": 2.5}
RAIN_WASH_MM = 3.0       # a day with this much rain washes the panels
EMISSION_KG_PER_KWH = 0.675  # CEA grid factor, as in the calculator
DEGRADATION = 0.005      # per year, inside the 25-year performance warranty
STEP_MIN = 10
# a typical Indian home's use through the day: a morning bump, a long evening peak (lights, fans, cooking, TV)
LOAD_SHAPE = [0.3, 0.25, 0.25, 0.25, 0.3, 0.45, 0.7, 0.9, 0.85, 0.6, 0.5, 0.55,
              0.6, 0.6, 0.55, 0.55, 0.6, 0.8, 1.1, 1.3, 1.35, 1.2, 0.9, 0.5]

TEXT = {
    "en": {
        "overvoltage": ("Grid voltage too high", "The inverter paused because the grid voltage at your home went above its limit. It usually happens at midday, when many rooftops export at once. It is the grid, not your panels.",
                        "Ask the DISCOM to check the transformer tap and the service line, and the installer to confirm the inverter's grid profile."),
        "undervoltage": ("Supply voltage too low", "The grid voltage fell below the inverter's range, so it stopped exporting until the voltage recovered.",
                         "If this repeats, ask the DISCOM to check the voltage at your meter; keep this log as evidence."),
        "outage": ("Power cut", "There was no grid supply, so the inverter shut down for safety. Ordinary on-grid solar does not run during a power cut.",
                   "Nothing to fix. If backup matters, ask for a hybrid inverter with a battery and price it separately."),
        "offline": ("Monitoring offline", "The Wi-Fi logger stopped sending data. The panels kept working; only the readings are missing.",
                    "Restart the Wi-Fi router, then the logger. If it keeps dropping, ask the installer to move it closer to the router."),
        "evidence": "On {day}, {start}–{end}: {title}. Inverter {model}, serial {serial}.",
    },
    "hi": {
        "overvoltage": ("ग्रिड वोल्टेज बहुत ज़्यादा", "आपके घर पर ग्रिड वोल्टेज सीमा से ऊपर गया, इसलिए इन्वर्टर रुक गया। यह अक्सर दोपहर में होता है जब कई छतें एक साथ बिजली भेजती हैं। यह ग्रिड की बात है, पैनल की नहीं।",
                        "DISCOM से ट्रांसफ़ॉर्मर टैप और सर्विस लाइन जाँचने को कहें, और इंस्टॉलर से इन्वर्टर का ग्रिड प्रोफ़ाइल पक्का करवाएँ।"),
        "undervoltage": ("सप्लाई वोल्टेज बहुत कम", "ग्रिड वोल्टेज इन्वर्टर की सीमा से नीचे गया, इसलिए वोल्टेज ठीक होने तक बिजली भेजना बंद रहा।",
                         "बार-बार हो तो DISCOM से मीटर पर वोल्टेज जाँचने को कहें; यह लॉग सबूत के तौर पर रखें।"),
        "outage": ("बिजली कटी", "ग्रिड सप्लाई नहीं थी, इसलिए सुरक्षा के लिए इन्वर्टर बंद हुआ। सामान्य ऑन-ग्रिड सोलर बिजली कटने पर नहीं चलता।",
                   "ठीक करने को कुछ नहीं। बैकअप चाहिए तो बैटरी वाला हाइब्रिड इन्वर्टर अलग से पूछें।"),
        "offline": ("निगरानी ऑफ़लाइन", "वाई-फ़ाई लॉगर ने डेटा भेजना बंद किया। पैनल चलते रहे; सिर्फ़ रीडिंग नहीं आई।",
                    "वाई-फ़ाई राउटर, फिर लॉगर दोबारा चालू करें। बार-बार हो तो इंस्टॉलर से लॉगर को राउटर के पास लगवाएँ।"),
        "evidence": "{day}, {start}–{end}: {title}। इन्वर्टर {model}, सीरियल {serial}।",
    },
}


def _fetch_json(url: str) -> dict:
    return product._fetch_json(url)


def _weather(lat: float, lon: float, fetch=None, now: float | None = None) -> dict:
    now = now or time.time()
    key = (round(lat, 2), round(lon, 2))
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_S:
        return hit[1]
    url = (f"{WEATHER_URL}?latitude={key[0]}&longitude={key[1]}&hourly=shortwave_radiation,temperature_2m,precipitation"
           "&daily=sunrise,sunset,weather_code,temperature_2m_max,precipitation_sum&past_days=31&forecast_days=4&timezone=Asia%2FKolkata")
    data = (fetch or _fetch_json)(url)
    _cache[key] = (now, data)
    return data


def _sky(code: int | None, rain_mm: float) -> str:
    if code is None:
        return "sun"
    if code >= 95:
        return "storm"
    if code >= 51 or rain_mm >= 2:
        return "rain"
    if code in (45, 48):
        return "haze"
    return "cloud" if code == 3 else "part" if code == 2 else "sun"


def power_kw(kw: float, ghi: float, temp_c: float, soil: float) -> float:
    """AC output for one moment: sunlight on the tilted panels, warmed cells, dust, then losses; capped at the inverter."""
    if ghi <= 0:
        return 0.0
    cell = temp_c + ghi * 0.03125
    p = kw * ghi * TILT_GAIN / 1000 * SYSTEM_LOSS * (1 + TEMP_COEFF * (cell - 25)) * (1 - soil)
    return max(0.0, min(kw, p))


def _seed(*parts) -> int:
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:12], 16)


def _events(site: str, day: str, sunrise: float, sunset: float) -> list[dict]:
    """The day's inverter events, the same for a home and a day every time; times in hours."""
    r = _seed(site, day)
    roll = r % 100
    out = []
    if roll < 26:  # owners report this most: export pushes the local voltage over the cut-off at midday
        start = 11.5 + (r >> 8) % 150 / 60
        out.append({"code": "overvoltage", "start": start, "end": start + (8 + (r >> 16) % 18) / 60, "volts": 253 + (r >> 20) % 6})
    elif roll < 34:
        start = sunrise + 1.5 + (r >> 8) % 120 / 60
        out.append({"code": "undervoltage", "start": start, "end": start + (6 + (r >> 16) % 14) / 60, "volts": 182 + (r >> 20) % 10})
    elif roll < 44:
        start = sunrise + 2 + (r >> 8) % int(max(60, (sunset - sunrise - 4) * 60)) / 60
        out.append({"code": "outage", "start": start, "end": start + (35 + (r >> 16) % 55) / 60})
    elif roll < 52:
        start = 9 + (r >> 8) % 300 / 60
        out.append({"code": "offline", "start": start, "end": start + (40 + (r >> 16) % 80) / 60})
    return out


def _hours(t: str) -> float:
    return int(t[11:13]) + int(t[14:16]) / 60


def _soiling(days: list[str], rain: dict, dust_level: dict, cleaned: date) -> dict:
    """Dust on the panels at the start of each day: builds daily, faster when dusty, washed off by rain or cleaning."""
    soil, out = 0.0, {}
    first = min(date.fromisoformat(days[0]), cleaned)
    d = first
    last = date.fromisoformat(days[-1])
    while d <= last:
        iso = d.isoformat()
        if d <= cleaned:
            soil = 0.0
        out[iso] = soil
        soil = 0.0 if rain.get(iso, 0) >= RAIN_WASH_MM else min(SOIL_CAP, soil + SOIL_PER_DAY * DUST_PACE.get(dust_level.get(iso, "clear"), 1.3))
        d += timedelta(days=1)
    return out


def simulate(kw: float = 3, lat: float = 28.61, lon: float = 77.21, cleaned: str | None = None, installed: str | None = None,
             rate: float = 7.0, promised: float | None = None, use: float = 300, fetch=None, dust=None, now: float | None = None,
             lang: str = "en") -> dict:
    kw = product.number(kw, "system size", 0.5, 20)
    lat = product.number(lat, "latitude", 6, 38)
    lon = product.number(lon, "longitude", 68, 98)
    rate = product.number(rate, "tariff", 1, 20)
    use = product.number(use, "monthly units", 30, 3000)
    now = now or time.time()
    here = datetime.fromtimestamp(now, IST)
    today = here.date()
    cleaned_on = date.fromisoformat(cleaned) if cleaned else today - timedelta(days=10)
    installed_on = date.fromisoformat(installed) if installed else today - timedelta(days=190)
    w = _weather(lat, lon, fetch, now)
    hourly, daily = w["hourly"], w["daily"]

    by_day: dict[str, list[tuple[float, float, float]]] = {}
    for t, ghi, temp in zip(hourly["time"], hourly["shortwave_radiation"], hourly["temperature_2m"]):
        # Open-Meteo's hourly sunlight is the mean of the hour before; centre it on the half hour
        by_day.setdefault(t[:10], []).append((_hours(t) - 0.5, ghi or 0.0, temp if temp is not None else 25.0))
    rain = {d: (p or 0.0) for d, p in zip(daily["time"], daily["precipitation_sum"])}
    if dust is None:
        try:
            dust = product.dust(lat, lon, now=now)
        except Exception:  # the dust forecast is a refinement; the plant still runs without it
            dust = {"days": []}
    dust_level = {d["date"]: d["level"] for d in dust.get("days", [])}
    soil = _soiling(daily["time"], rain, dust_level, cleaned_on)
    site = f"{lat:.2f},{lon:.2f},{kw:g}"
    serial = f"SIM{_seed(site) % 10**8:08d}"
    model = f"SG{kw:g}K-SIM"

    def curve(day: str, with_events: bool, with_soil: bool = True) -> list[tuple[float, float]]:
        pts = by_day.get(day, [])
        i = daily["time"].index(day) if day in daily["time"] else None
        rise = _hours(daily["sunrise"][i]) if i is not None else 6.25
        sett = _hours(daily["sunset"][i]) if i is not None else 18.0
        evs = _events(site, day, rise, sett) if with_events else []
        out, h = [], rise
        while h <= sett + 1e-9:
            ghi, temp = _interp(pts, h)
            p = power_kw(kw, ghi, temp, soil.get(day, 0.0) if with_soil else 0.0)
            if any(e["start"] <= h < e["end"] and e["code"] != "offline" for e in evs):
                p = 0.0
            out.append((round(h, 3), round(p, 3)))
            h += STEP_MIN / 60
        return out

    def energy(points: list[tuple[float, float]], until: float = 99) -> float:
        return sum(p for h, p in points if h <= until) * STEP_MIN / 60

    day_iso = today.isoformat()
    hour_now = here.hour + here.minute / 60
    i_today = daily["time"].index(day_iso)
    sunrise, sunset = _hours(daily["sunrise"][i_today]), _hours(daily["sunset"][i_today])
    actual, clean = curve(day_iso, True), curve(day_iso, False, with_soil=False)
    ahead_today = curve(day_iso, False)  # the rest of today is a forecast: tomorrow's events aren't known yet
    events_today = _events(site, day_iso, sunrise, sunset)
    live_event = next((e for e in events_today if e["start"] <= hour_now < e["end"]), None)
    power_now = 0.0 if not sunrise <= hour_now <= sunset else _at(actual, hour_now)
    status = ("night" if not sunrise <= hour_now <= sunset else live_event["code"] if live_event else "producing")

    # the month so far, from the past month's real weather
    days_done = [d for d in daily["time"] if d < day_iso]
    past = {d: energy(curve(d, True)) for d in days_done}
    month_days = [d for d in days_done if d[:7] == day_iso[:7]]
    today_so_far = energy(actual, hour_now)
    month_kwh = sum(past[d] for d in month_days) + today_so_far
    recent = [past[d] for d in days_done[-30:]] or [kw * 4]
    avg_day = sum(recent) / len(recent)
    life_days = max(0, (today - installed_on).days)
    counted = [d for d in days_done if d >= installed_on.isoformat()]
    lifetime_kwh = sum(past[d] for d in counted) + max(0, life_days - len(counted)) * avg_day + today_so_far
    days_in_month = (date(today.year + today.month // 12, today.month % 12 + 1, 1) - timedelta(days=1)).day
    forecast_days = [d for d in daily["time"] if d > day_iso][:3]
    ahead = {d: energy(curve(d, False)) for d in forecast_days}
    rest_today = sum(p for h, p in ahead_today if h > hour_now) * STEP_MIN / 60
    in_month = [d for d in forecast_days if d[:7] == day_iso[:7]]
    projected = month_kwh + rest_today + sum(ahead[d] for d in in_month) + max(0, days_in_month - today.day - len(in_month)) * avg_day

    # where today's solar went: used at home first, the rest sent to the grid; the shortfall bought back
    per_day = use * 12 / 365
    load = lambda h: per_day * LOAD_SHAPE[int(h) % 24] / sum(LOAD_SHAPE)
    self_used = exported = imported = 0.0
    step = STEP_MIN / 60
    for h, solar in actual:  # the same points the day's total is made of
        if h > hour_now:
            break
        need = load(h)
        self_used += min(solar, need) * step
        exported += max(0.0, solar - need) * step
        imported += max(0.0, need - solar) * step
    dark = [x * step for x in range(int(hour_now / step) + 1) if x * step < sunrise or x * step > sunset]
    imported += sum(load(h) for h in dark) * step  # before sunrise and after sunset, everything is bought
    home_now = load(hour_now)

    # dust: what it costs today, and the day to clean
    loss_today = max(0.0, energy(clean) - energy(curve(day_iso, False)))
    t = TEXT[lang if lang in TEXT else "en"]

    def event_view(e: dict, day: str) -> dict:
        title, meaning, todo = t[e["code"]]
        clock = lambda h: f"{int(h):02d}:{int(round(h % 1 * 60)) % 60:02d}"
        when = date.fromisoformat(day).strftime("%d %b")
        return {"code": e["code"], "day": day, "start": clock(e["start"]), "end": clock(e["end"]), "volts": e.get("volts"),
                "title": title, "meaning": meaning, "todo": todo,
                "evidence": t["evidence"].format(day=when, start=clock(e["start"]), end=clock(e["end"]),
                                                  title=title + (f" ({e['volts']} V)" if e.get("volts") else ""), model=model, serial=serial)}

    log = []
    for d in [*days_done[-6:], day_iso]:
        i = daily["time"].index(d)
        for e in _events(site, d, _hours(daily["sunrise"][i]), _hours(daily["sunset"][i])):
            if d < day_iso or e["start"] <= hour_now:
                log.append(event_view(e, d))
    log.reverse()

    years = []
    annual = avg_day * 365
    for y in range(1, 26):
        units = annual * (1 - DEGRADATION * (y - 1))
        years.append({"year": installed_on.year + y - 1, "units": round(units), "share": round(1 - DEGRADATION * (y - 1), 3)})

    def due(on: date, what: str) -> dict:
        return {"what": what, "on": on.isoformat(), "in_days": (on - today).days}

    clean_on = dust.get("clean_on")
    return {
        "simulated": True,
        "device": {"model": model, "serial": serial, "firmware": "V3.2.1", "logger": "Wi-Fi", "kw": kw,
                   "installed": installed_on.isoformat(), "cleaned": cleaned_on.isoformat()},
        "now": {"time": here.strftime("%H:%M"), "hour": round(hour_now, 3), "status": status, "power_kw": round(power_now, 2),
                "event": event_view(live_event, day_iso) if live_event else None,
                "home_kw": round(home_now, 2), "grid_kw": round(power_now - home_now, 2)},
        "today": {"date": day_iso, "sunrise": round(sunrise, 3), "sunset": round(sunset, 3),
                  "points": [{"h": h, "kw": p if h <= hour_now else f, "clean_kw": c, "home_kw": round(load(h), 3), "ahead": h > hour_now}
                             for (h, p), (_, c), (_, f) in zip(actual, clean, ahead_today)],
                  "gaps": [{"start": e["start"], "end": min(e["end"], hour_now)} for e in events_today
                           if e["code"] == "offline" and e["start"] <= hour_now],
                  "so_far_kwh": round(today_so_far, 1), "day_kwh": round(today_so_far + rest_today, 1), "clean_kwh": round(energy(clean), 1),
                  "saved_rs": round(today_so_far * rate), "dust_loss_kwh": round(loss_today, 2), "dust_loss_rs": round(loss_today * rate),
                  "soiling_pct": round(soil.get(day_iso, 0) * 100, 1),
                  "self_used_kwh": round(self_used, 1), "exported_kwh": round(exported, 1), "imported_kwh": round(imported, 1)},
        "ahead": [{"date": d, "kwh": round(ahead[d], 1), "rs": round(ahead[d] * rate),
                   "sky": _sky(daily["weather_code"][daily["time"].index(d)], rain.get(d, 0)),
                   "max_c": daily["temperature_2m_max"][daily["time"].index(d)], "rain_mm": round(rain.get(d, 0), 1),
                   "dust": dust_level.get(d)} for d in forecast_days],
        "history": [{"date": d, "kwh": round(past[d], 1)} for d in days_done[-14:]],
        "month": {"kwh": round(month_kwh), "rs": round(month_kwh * rate), "projected_kwh": round(projected),
                  "promised_kwh": promised, "on_track_pct": round(projected / promised * 100) if promised else None},
        "lifetime": {"kwh": round(lifetime_kwh), "rs": round(lifetime_kwh * rate), "co2_t": round(lifetime_kwh * EMISSION_KG_PER_KWH / 1000, 2),
                     "trees": round(lifetime_kwh * EMISSION_KG_PER_KWH / 21), "days": life_days},
        "care": {"clean_on": clean_on, "dust_advice": dust.get("advice"),
                 "rain_wash": next((d for d in forecast_days if rain.get(d, 0) >= RAIN_WASH_MM), None),
                 "next": sorted([due(date(today.year + today.month // 12, today.month % 12 + 1, 1), "bill_check"),
                                 due(installed_on + timedelta(days=365 * ((today - installed_on).days // 365 + 1)), "inspection"),
                                 due(date(today.year + (today.month + 2) // 12, (today.month + 2) % 12 + 1, 1), "earthing"),
                                 due(installed_on + timedelta(days=365 * 5), "workmanship_warranty")],
                                key=lambda x: x["in_days"])},
        "events": log,
        "years": years,
        "rate": rate, "use": use,
    }


def _interp(pts: list[tuple[float, float, float]], h: float) -> tuple[float, float]:
    if not pts:
        return 0.0, 25.0
    for (h1, g1, t1), (h2, g2, t2) in zip(pts, pts[1:]):
        if h1 <= h <= h2:
            f = (h - h1) / (h2 - h1)
            return g1 + (g2 - g1) * f, t1 + (t2 - t1) * f
    return (pts[0][1], pts[0][2]) if h < pts[0][0] else (pts[-1][1], pts[-1][2])


def _at(points: list[tuple[float, float]], h: float) -> float:
    for (h1, p1), (h2, p2) in zip(points, points[1:]):
        if h1 <= h <= h2:
            return p1 + (p2 - p1) * (h - h1) / (h2 - h1)
    return 0.0
