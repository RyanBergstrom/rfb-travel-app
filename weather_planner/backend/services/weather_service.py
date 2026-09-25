import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import httpx

from .scoring_service import calculate_hiking_score, score_color

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


def c_to_f(celsius: float) -> float:
    return round(celsius * 9 / 5 + 32, 1)


def km_to_miles(km: float) -> float:
    return round(km * 0.621371, 1)


async def fetch_raw_forecast(
    latitude: float, longitude: float, days: int = 7
) -> Optional[dict]:
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


async def fetch_forecast_batch(
    locations: list[dict], days: int = 7
) -> dict[str, Optional[dict]]:
    async def _fetch_one(loc):
        try:
            return loc["id"], await fetch_raw_forecast(
                loc["latitude"], loc["longitude"], days
            )
        except Exception:
            return loc["id"], None

    results = await asyncio.gather(*[_fetch_one(loc) for loc in locations])
    return dict(results)


def aggregate_period(
    hourly_data: dict, date_str: str, period_name: str
) -> Optional[dict]:
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

    def avg(field: str) -> float:
        values = [hourly_data[field][i] for i in indices if hourly_data[field][i] is not None]
        return round(sum(values) / len(values), 1) if values else 0

    temp_c = avg("temperature_2m")
    temp_f = c_to_f(temp_c)
    wind_mph = km_to_miles(avg("wind_speed_10m"))
    gust_mph = km_to_miles(avg("wind_gusts_10m"))
    rain_prob = avg("precipitation_probability")
    rain_mm = avg("precipitation")
    rain_in = round(rain_mm / 25.4, 2)
    visibility_m = avg("visibility")
    cloud_cover = avg("cloud_cover")

    score = calculate_hiking_score(
        temperature_f=temp_f,
        wind_speed_mph=wind_mph,
        rain_probability=rain_prob,
        cloud_cover=cloud_cover,
        visibility_m=visibility_m,
    )

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


def aggregate_forecast(
    raw_forecast: dict, location_id: str
) -> List[dict]:
    if not raw_forecast or "hourly" not in raw_forecast:
        return []

    hourly = raw_forecast["hourly"]
    times = hourly.get("time", [])

    dates = sorted(set(t.split("T")[0] for t in times))
    dates = dates[:7]

    results = []
    for date_str in dates:
        for period_name in ["Morning", "Afternoon", "Evening"]:
            agg = aggregate_period(hourly, date_str, period_name)
            if agg:
                results.append(
                    {
                        "locationId": location_id,
                        "date": date_str,
                        "period": period_name,
                        **agg,
                    }
                )

    return results
