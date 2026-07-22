# AGENTS.md — RFB Travel App

## Stack
- **Backend**: Python + FastAPI + DuckDB
- **Frontend**: Single `index.html` (vanilla JS, mobile-first CSS)
- **Python**: 3.14 at `C:\Users\urfb2\AppData\Local\Python\bin\python.exe`

## Commands
```powershell
# Run server (from repo root)
& "C:\Users\urfb2\AppData\Local\Python\bin\python.exe" backend/server.py
# → http://localhost:8000

# Ingest a HAR file
& "C:\Users\urfb2\AppData\Local\Python\bin\python.exe" -c "import sys; sys.path.insert(0, 'backend'); from ingest_coop import ingest_har; ingest_har('harfiles/yourfile.har')"
```

## Project structure
```
backend/
  server.py          — FastAPI app (search API + serves frontend)
  database.py        — DuckDB init, insert, search helpers
  ingest_coop.py     — HAR parser for coop.ch (SAP Hybris HTML)
  converter.py       — CHF→USD + metric→US units
frontend/
  index.html         — Single-page mobile search UI
data/
  travel_prices.duckdb
harfiles/
  www.coop.ch.har    — Sample HAR (98 products, fruit/veg)
```

## HAR parsing
The coop.ch HAR parser extracts product data from the `data-pagecontent-json` meta tag in the HTML response (entry[0]). It finds the `productTile` anchor and reads `elements` array. Each element has: `id`, `title`, `price`, `currency` (CHF), `quantity` (e.g. `500g`, `1PCE`), `priceContext` (e.g. `0.50/100g`), `image.src`.

## Adding a new site parser
1. Create `backend/ingest_<site>.py` with an `extract_products_from_har(path)` function returning the same dict format.
2. Import it in the ingestion script and call `insert_product(conn, p)`.

## Currency & units
- CHF→USD rate: `1.12` (hardcoded in `converter.py`)
- Conversions: g→oz, kg→lb, ml→fl oz, l→qt, PCE→piece, Bd→bunch
- Display: < 1 lb shown as oz, >= 1 qt shown as gal
