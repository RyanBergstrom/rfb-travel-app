import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'weather_planner'))

import json
import time
import traceback

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from database import init_db, search_products, get_all_products, product_count, get_categories, get_sources, get_connection
from converter import convert_product

WEATHER_CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'weather_planner', 'backend', 'cache', 'forecast_cache.json')
CACHE_TTL_SECONDS = 2 * 60 * 60  # 2 hours

app = FastAPI(title="Travel Price Search")

IS_PRODUCTION = bool(os.environ.get('RENDER'))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_cache() -> dict | None:
    if not os.path.exists(WEATHER_CACHE_PATH):
        return None
    try:
        with open(WEATHER_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_cache(data: dict) -> None:
    os.makedirs(os.path.dirname(WEATHER_CACHE_PATH), exist_ok=True)
    with open(WEATHER_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _cache_is_valid() -> bool:
    cached = _read_cache()
    if not cached or "timestamp" not in cached:
        return False
    return (time.time() - cached["timestamp"]) < CACHE_TTL_SECONDS


@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/search")
def search(q: str = Query("", min_length=0), cat: str = Query("", min_length=0), src: str = Query("", min_length=0), limit: int = 50):
    if not q.strip() and not cat.strip() and not src.strip():
        products = get_all_products()
    else:
        products = search_products(q, cat, src, limit)
    return [convert_product(p) for p in products]

@app.get("/api/categories")
def categories(src: str = Query("", min_length=0)):
    return get_categories(src)

@app.get("/api/sources")
def sources():
    return get_sources()

@app.get("/api/count")
def count():
    return {"count": product_count()}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/sql/tables")
def sql_tables():
    if IS_PRODUCTION:
        return JSONResponse({"error": "Admin API disabled in production"}, status_code=403)
    try:
        conn = get_connection()
        results = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name").fetchall()
        conn.close()
        return {"tables": [r[0] for r in results]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/sql")
async def run_sql(req: Request):
    if IS_PRODUCTION:
        return JSONResponse({"error": "Admin API disabled in production"}, status_code=403)
    body = await req.json()
    sql = body.get("sql", "").strip()
    if not sql:
        return JSONResponse({"error": "No SQL provided"}, status_code=400)
    try:
        conn = get_connection()
        result = conn.execute(sql)
        if result.description:
            columns = [desc[0] for desc in result.description]
            rows = [list(row) for row in result.fetchall()]
            conn.close()
            return {"columns": columns, "rows": rows, "row_count": len(rows)}
        else:
            conn.close()
            return {"affected": True}
    except Exception as e:
        return JSONResponse({"error": traceback.format_exc()}, status_code=400)

@app.get("/", response_class=HTMLResponse)
def frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    with open(frontend_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
def admin():
    admin_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'sql.html')
    with open(admin_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/weather", response_class=HTMLResponse)
def weather_planner():
    weather_path = os.path.join(os.path.dirname(__file__), '..', 'weather_planner', 'frontend', 'dist', 'index.html')
    if os.path.exists(weather_path):
        with open(weather_path, 'r', encoding='utf-8') as f:
            return f.read()
    dev_path = os.path.join(os.path.dirname(__file__), '..', 'weather_planner', 'frontend', 'index.html')
    with open(dev_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/api/weather/locations")
def weather_locations():
    from backend.services.location_service import get_enabled_locations
    return get_enabled_locations()


async def _refresh_weather_cache() -> dict:
    from backend.services.location_service import get_enabled_locations
    from backend.services.weather_service import fetch_forecast_batch, aggregate_forecast
    locations = get_enabled_locations()
    raw_data = await fetch_forecast_batch(locations)
    all_forecasts = []
    success_count = 0
    for loc in locations:
        raw = raw_data.get(loc["id"])
        if raw:
            success_count += 1
            all_forecasts.extend(aggregate_forecast(raw, loc["id"]))
    cache_data = {
        "timestamp": time.time(),
        "forecasts": all_forecasts,
        "locationCount": len(locations),
        "locationsRefreshed": success_count,
    }
    _write_cache(cache_data)
    return cache_data


@app.get("/api/weather/forecast")
async def weather_forecast(location_id: str = Query(None)):
    cached = _read_cache()
    if _cache_is_valid() and cached and "forecasts" in cached:
        forecasts = cached["forecasts"]
    else:
        cache_data = await _refresh_weather_cache()
        forecasts = cache_data["forecasts"]

    if location_id:
        forecasts = [f for f in forecasts if f["locationId"] == location_id]

    return {"forecasts": forecasts, "locationCount": len(set(f["locationId"] for f in forecasts))}


@app.post("/api/weather/refresh")
async def weather_refresh():
    cache_data = await _refresh_weather_cache()
    return {
        "status": "refreshed",
        "locationsRefreshed": cache_data["locationsRefreshed"],
        "totalLocations": cache_data["locationCount"],
    }

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
