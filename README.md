---
title: Travel Price Search
emoji: 🌍
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Travel Price Search

Search product prices from Swiss grocery stores, converted to USD and US measurements.

## Local dev

```bash
pip install -r requirements.txt
python backend/server.py
# → http://localhost:8000
```

## Ingest a HAR file

```bash
python -c "import sys; sys.path.insert(0, 'backend'); from ingest_coop import ingest_har; ingest_har('harfiles/yourfile.har')"
```
