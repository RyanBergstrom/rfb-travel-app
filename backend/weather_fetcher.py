import asyncio
import json
import os
import time

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_FIELDS = [
    "temperature_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "rain",
    "wind_speed_10m",
    "wind_gusts_10m",
    "cloud_cover",
    "visibility",
    "weather_code",
]

PERIOD_RANGES = {
    "Morning": (6, 11),
    "Afternoon": (12, 17),
    "Evening": (18, 23),
}

LOCATIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'weather_planner', 'backend', 'config', 'locations.json')
CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'weather_planner', 'backend', 'cache', 'forecast_cache.json')
CACHE_TTL = 2 * 60 * 60


def load_locations():
    with open(LOCATIONS_PATH, 'r') as f:
        return [loc for loc in json.load(f) if loc.get('enabled', True)]


def read_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def write_cache(data):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def cache_is_valid():
    cached = read_cache()
    if not cached or "timestamp" not in cached:
        return False
    return (time.time() - cached["timestamp"]) < CACHE_TTL


def c_to_f(celsius):
    return round(celsius * 9 / 5 + 32, 1)


def km_to_miles(km):
    return round(km * 0.621371, 1)


def calculate_hiking_score(temperature_f, wind_speed_mph, rain_probability, cloud_cover, visibility_m):
    score = 100.0
    score -= rain_probability * 0.40
    score -= wind_speed_mph * 1.50
    score -= cloud_cover * 0.15
    visibility_km = visibility_m / 1000.0
    if visibility_km > 25:
        score += 20
    elif visibility_km > 15:
        score += 10
    if 50 <= temperature_f <= 68:
        score += 10
    return max(0, min(100, int(round(score))))


def score_color(score):
    if score >= 75:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


async def fetch_raw_forecast(latitude, longitude, days=7):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(HOURLY_FIELDS),
        "forecast_days": days,
        "timezone": "Europe/London",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        return resp.json()


async def fetch_forecast_batch(locations, days=7):
    async def _fetch_one(loc):
        try:
            return loc["id"], await fetch_raw_forecast(loc["latitude"], loc["longitude"], days)
        except Exception:
            return loc["id"], None

    results = await asyncio.gather(*[_fetch_one(loc) for loc in locations])
    return dict(results)


def aggregate_period(hourly_data, date_str, period_name):
    hour_start, hour_end = PERIOD_RANGES[period_name]
    times = hourly_data.get("time", [])
    indices = []
    for i, t in enumerate(times):
        if t.startswith(date_str):
            hour = int(t.split("T")[1].split(":")[0])
            if hour_start <= hour <= hour_end:
                indices.append(i)
    if not indices:
        return None

    def avg(field):
        values = [hourly_data[field][i] for i in indices if hourly_data[field][i] is not None]
        return round(sum(values) / len(values), 1) if values else 0

    temp_f = c_to_f(avg("temperature_2m"))
    wind_mph = km_to_miles(avg("wind_speed_10m"))
    gust_mph = km_to_miles(avg("wind_gusts_10m"))
    rain_prob = avg("precipitation_probability")
    rain_in = round(avg("precipitation") / 25.4, 2)
    visibility_m = avg("visibility")
    cloud_cover = avg("cloud_cover")

    score = calculate_hiking_score(temp_f, wind_mph, rain_prob, cloud_cover, visibility_m)

    return {
        "temperature": temp_f,
        "wind": wind_mph,
        "gust": gust_mph,
        "rainProbability": rain_prob,
        "rainAmount": rain_in,
        "visibility": round(visibility_m / 1000, 1),
        "cloudCover": cloud_cover,
        "score": score,
        "scoreColor": score_color(score),
    }


def aggregate_forecast(raw_forecast, location_id):
    if not raw_forecast or "hourly" not in raw_forecast:
        return []
    hourly = raw_forecast["hourly"]
    times = hourly.get("time", [])
    dates = sorted(set(t.split("T")[0] for t in times))[:7]
    results = []
    for date_str in dates:
        for period_name in ["Morning", "Afternoon", "Evening"]:
            agg = aggregate_period(hourly, date_str, period_name)
            if agg:
                results.append({"locationId": location_id, "date": date_str, "period": period_name, **agg})
    return results


async def refresh_all(force=False):
    locations = load_locations()
    raw_data = await fetch_forecast_batch(locations)
    all_forecasts = []
    success_count = 0
    failed_ids = []
    for loc in locations:
        raw = raw_data.get(loc["id"])
        if raw:
            success_count += 1
            all_forecasts.extend(aggregate_forecast(raw, loc["id"]))
        else:
            failed_ids.append(loc["id"])

    if failed_ids and not force:
        cached = read_cache()
        if cached and "forecasts" in cached:
            existing_ids = set(f["locationId"] for f in cached["forecasts"])
            for f in all_forecasts:
                if f["locationId"] not in existing_ids:
                    cached["forecasts"].append(f)
            cached["locationsRefreshed"] = success_count
            cached["timestamp"] = time.time()
            write_cache(cached)
            return cached

    cache_data = {
        "timestamp": time.time(),
        "forecasts": all_forecasts,
        "locationCount": len(locations),
        "locationsRefreshed": success_count,
    }
    write_cache(cache_data)
    return cache_data
