from fastapi import APIRouter
from ..services.location_service import get_enabled_locations
from ..services.weather_service import fetch_forecast_batch
from ..services.cache_service import CacheService

router = APIRouter(prefix="/api", tags=["refresh"])

cache = CacheService()


@router.post("/refresh")
async def refresh_weather():
    locations = get_enabled_locations()
    raw_data = await fetch_forecast_batch(locations)

    cache.invalidate_all()

    success_count = sum(1 for v in raw_data.values() if v is not None)

    return {
        "status": "refreshed",
        "locationsRefreshed": success_count,
        "totalLocations": len(locations),
    }
