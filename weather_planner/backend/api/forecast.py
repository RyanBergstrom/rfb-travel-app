from fastapi import APIRouter, Query
from typing import Optional
from ..services.location_service import get_enabled_locations, get_location_by_id
from ..services.weather_service import fetch_raw_forecast, aggregate_forecast
from ..services.cache_service import CacheService

router = APIRouter(prefix="/api", tags=["forecast"])

cache = CacheService()


@router.get("/forecast")
async def get_forecast(
    location_id: Optional[str] = Query(None, description="Specific location ID"),
    days: int = Query(7, ge=1, le=7),
):
    locations = get_enabled_locations()

    if location_id:
        loc = get_location_by_id(location_id)
        if not loc:
            return {"error": "Location not found"}
        locations = [loc]

    cache_key = f"forecast_{days}"
    cached = cache.get(cache_key)

    results = []
    for loc in locations:
        loc_cache_key = f"{cache_key}_{loc['id']}"
        if cached and loc["id"] in cached:
            raw = cached[loc["id"]]
        else:
            raw = await fetch_raw_forecast(loc["latitude"], loc["longitude"], days)

        forecasts = aggregate_forecast(raw, loc["id"])
        results.extend(forecasts)

    return {
        "forecasts": results,
        "locationCount": len(locations),
    }
