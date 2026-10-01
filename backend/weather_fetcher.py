import asyncio
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

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

# Semaphore to limit concurrent requests to Open-Meteo (rate limiting)
RATE_LIMITER = asyncio.Semaphore(2)


def load_locations():
    try:
        with open(LOCATIONS_PATH, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(f"ERROR: locations.json is not a list; got {type(data)}")
            return []
        enabled = [loc for loc in data if loc.get('enabled', True)]
        print(f"Loaded {len(enabled)} enabled locations")
        return enabled
    except FileNotFoundError:
        print(f"ERROR: locations.json not found at {LOCATIONS_PATH}")
        return []
    except Exception as e:
        print(f"ERROR loading locations.json: {e}")
        return []


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


async def fetch_raw_forecast(location_id, latitude, longitude, days=7):
    async with RATE_LIMITER:
        await asyncio.sleep(0.5)  # 0.5s delay between requests
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(HOURLY_FIELDS),
            "forecast_days": days,
            "timezone": "Europe/London",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(OPEN_METEO_URL, params=params)
                resp.raise_for_status()
                payload = resp.json()
                if not payload.get("hourly") or not payload["hourly"].get("time"):
                    print(f"WARNING: {location_id} returned no hourly data")
                    return None
                return payload
        except Exception as e:
            print(f"ERROR fetching forecast for {location_id} ({latitude}, {longitude}): {e}")
            return None


async def fetch_forecast_batch(locations, days=7):
    async def _fetch_one(loc):
        loc_id = loc.get("id")
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        if lat is None or lon is None:
            print(f"ERROR: location {loc_id} missing latitude/longitude")
            return loc_id, None
        return loc_id, await fetch_raw_forecast(loc_id, lat, lon, days)

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

    london_tz = ZoneInfo("Europe/London")
    today_str = datetime.now(london_tz).date().isoformat()
    dates = sorted(set(t.split("T")[0] for t in times if t.split("T")[0] >= today_str))[:7]

    results = []
    for date_str in dates:
        for period_name in ["Morning", "Afternoon", "Evening"]:
            agg = aggregate_period(hourly, date_str, period_name)
            if agg:
                results.append({"locationId": location_id, "date": date_str, "period": period_name, **agg})
    return results


async def refresh_all(force=False):
    locations = load_locations()
    if not locations:
        print("ERROR: no locations loaded; forecast refresh aborted")
        return {"forecasts": [], "locationCount": 0, "locationsRefreshed": 0}

    print(f"Refreshing forecast for {len(locations)} locations (rate limited to 2 concurrent requests)")
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

    print(f"Refresh complete: succeeded={success_count}, failed={len(failed_ids)}, forecast_rows={len(all_forecasts)}")

    if failed_ids and not force:
        cached = read_cache()
        if cached and "raw_forecasts" in cached:
            for loc_id, raw in cached["raw_forecasts"].items():
                if raw and loc_id not in [f["locationId"] for f in all_forecasts]:
                    all_forecasts.extend(aggregate_forecast(raw, loc_id))
            cached_data = {
                "timestamp": time.time(),
                "forecasts": all_forecasts,
                "raw_forecasts": cached.get("raw_forecasts", {}),
                "locationCount": len(locations),
                "locationsRefreshed": success_count,
            }
            write_cache(cached_data)
            return cached_data

    raw_forecasts = {}
    for loc in locations:
        if loc["id"] in raw_data and raw_data[loc["id"]]:
            raw_forecasts[loc["id"]] = raw_data[loc["id"]]

    cache_data = {
        "timestamp": time.time(),
        "forecasts": all_forecasts,
        "raw_forecasts": raw_forecasts,
        "locationCount": len(locations),
        "locationsRefreshed": success_count,
    }
    write_cache(cache_data)
    return cache_data
