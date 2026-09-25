import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import json
import time
import traceback

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from database import init_db, search_products, get_all_products, product_count, get_categories, get_sources, get_connection
from converter import convert_product
from weather_fetcher import load_locations, read_cache, write_cache, cache_is_valid, refresh_all

app = FastAPI(title="Travel Price Search")

IS_PRODUCTION = bool(os.environ.get('RENDER'))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

weather_dist = os.path.join(os.path.dirname(__file__), '..', 'weather_planner', 'frontend', 'dist')
if os.path.isdir(weather_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(weather_dist, "assets")), name="weather-assets")

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
    return load_locations()

@app.get("/api/weather/forecast")
async def weather_forecast(location_id: str = Query(None)):
    cached = read_cache()
    if cache_is_valid() and cached and "forecasts" in cached:
        forecasts = cached["forecasts"]
    else:
        cache_data = await refresh_all()
        forecasts = cache_data["forecasts"]

    if location_id:
        forecasts = [f for f in forecasts if f["locationId"] == location_id]

    return {"forecasts": forecasts, "locationCount": len(set(f["locationId"] for f in forecasts))}


@app.get("/api/weather/forecast/stream")
async def weather_forecast_stream():
    from weather_fetcher import load_locations, read_cache, cache_is_valid, refresh_all, fetch_forecast_batch, aggregate_forecast, write_cache
    import asyncio, json, time

    cached = read_cache()
    if cache_is_valid() and cached and "forecasts" in cached:
        def send_cached():
            yield f"event: forecast\ndata: {json.dumps({'forecasts': cached['forecasts'], 'locationCount': len(set(f['locationId'] for f in cached['forecasts'])), 'progress': 100, 'loaded': len(cached['forecasts']), 'total': len(cached['forecasts'])})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
        return StreamingResponse(send_cached(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    locations = load_locations()
    total = len(locations)
    BATCH_SIZE = 5

    async def event_generator():
        all_forecasts = []
        for i in range(0, total, BATCH_SIZE):
            batch = locations[i:i + BATCH_SIZE]
            raw_data = await fetch_forecast_batch(batch)
            batch_forecasts = []
            for loc in batch:
                raw = raw_data.get(loc["id"])
                if raw:
                    batch_forecasts.extend(aggregate_forecast(raw, loc["id"]))
            all_forecasts.extend(batch_forecasts)
            loaded = min(i + BATCH_SIZE, total)
            progress = int(loaded / total * 100)
            yield f"event: forecast\ndata: {json.dumps({'forecasts': batch_forecasts, 'progress': progress, 'loaded': loaded, 'total': total, 'batchIndex': i // BATCH_SIZE})}\n\n"

        cache_data = {
            "timestamp": time.time(),
            "forecasts": all_forecasts,
            "locationCount": total,
            "locationsRefreshed": sum(1 for f in all_forecasts if f),
        }
        write_cache(cache_data)
        yield f"event: done\ndata: {json.dumps({'totalForecasts': len(all_forecasts)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.post("/api/weather/refresh")
async def weather_refresh():
    cache_data = await refresh_all()
    return {
        "status": "refreshed",
        "locationsRefreshed": cache_data["locationsRefreshed"],
        "totalLocations": cache_data["locationCount"],
    }

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
