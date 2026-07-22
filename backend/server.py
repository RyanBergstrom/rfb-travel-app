import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import json
import traceback

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from database import init_db, search_products, get_all_products, product_count, get_categories, get_sources, get_connection
from converter import convert_product

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

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
