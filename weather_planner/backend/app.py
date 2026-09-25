from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.locations import router as locations_router
from .api.forecast import router as forecast_router
from .api.refresh import router as refresh_router
from .services.cache_service import CacheService
from .services.location_service import get_enabled_locations
from .services.weather_service import fetch_forecast_batch

cache = CacheService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _refresh_all()
    yield


app = FastAPI(
    title="Scotland Weather Planner",
    description="Weather intelligence for Scottish hiking destinations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(locations_router)
app.include_router(forecast_router)
app.include_router(refresh_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "scotland-weather-planner"}


@app.post("/api/refresh-all")
async def refresh_all():
    return await _refresh_all()


async def _refresh_all():
    locations = get_enabled_locations()
    raw_data = await fetch_forecast_batch(locations)

    for loc_id, raw in raw_data.items():
        if raw:
            cache.set(f"forecast_7_{loc_id}", raw)

    return {
        "status": "refreshed",
        "locationsRefreshed": sum(1 for v in raw_data.values() if v is not None),
        "totalLocations": len(locations),
    }
