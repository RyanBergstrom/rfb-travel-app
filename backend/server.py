import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from database import init_db, search_products, get_all_products, product_count, get_categories
from converter import convert_product

app = FastAPI(title="Travel Price Search")

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
def search(q: str = Query("", min_length=0), cat: str = Query("", min_length=0), limit: int = 50):
    if not q.strip() and not cat.strip():
        products = get_all_products()
    else:
        products = search_products(q, cat, limit)
    return [convert_product(p) for p in products]

@app.get("/api/categories")
def categories():
    return get_categories()

@app.get("/api/count")
def count():
    return {"count": product_count()}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    with open(frontend_path, 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
