import urllib.request
import json
import time
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from database import get_connection, init_db, insert_product

API_BASE = 'https://api.aldi-sued.de/v3/product-search'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Origin': 'https://www.aldi-sued.de',
    'Referer': 'https://www.aldi-sued.de/produkte',
}
SOURCE = 'aldi-sued'

def _fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read().decode('utf-8'))

def get_categories():
    data = _fetch(f'{API_BASE}?page=1')
    facets = data['meta']['facets']
    for f in facets:
        if f['name'] == 'category-tree':
            cats = []
            for v in f['values']:
                if v.get('children'):
                    for c in v['children']:
                        cats.append({
                            'id': c['key'],
                            'name': c['label'],
                            'count': c['docCount'],
                        })
                else:
                    cats.append({
                        'id': v['key'],
                        'name': v['label'],
                        'count': v['docCount'],
                    })
            return cats
    return []

def fetch_category_products(category_id):
    products = []
    offset = 0
    while True:
        url = f'{API_BASE}?categoryTree={category_id}&offset={offset}'
        try:
            data = _fetch(url)
        except Exception as e:
            print(f'  Error at offset {offset}: {e}')
            break
        items = data.get('data', [])
        if not items:
            break
        products.extend(items)
        pag = data['meta']['pagination']
        total = pag.get('totalCount', 0)
        offset += len(items)
        if offset >= total:
            break
        time.sleep(0.2)
    return products

def make_image_url(asset, slug):
    url = asset.get('url', '')
    if not url:
        return None
    url = url.replace('{width}', '200')
    url = url.replace('{slug}', slug)
    mime = asset.get('mimeType', '')
    if mime == 'image/*':
        url = url.replace('jpg/scaleWidth', 'jpg') if '/jpg/' in url else url
    return url

def extract_per_unit(comparison_display):
    if not comparison_display:
        return None
    m = re.search(r'[\d.,]+\s*\u20ac\s*/\s*(.+)', comparison_display)
    if m:
        return m.group(1).strip()
    m = re.search(r'/\s*(.+)$', comparison_display)
    if m:
        return m.group(1).strip()
    return None

def map_product(p):
    price = p.get('price', {})
    amount_raw = price.get('amount', 0)
    if not amount_raw:
        return None

    price_eur = round(float(amount_raw) / 100, 2)
    price_per_unit_eur = None
    per_unit = None

    comparison_raw = price.get('comparison')
    if comparison_raw:
        price_per_unit_eur = round(float(comparison_raw) / 100, 2)
        per_unit = extract_per_unit(price.get('comparisonDisplay', ''))

    categories = p.get('categories', [])
    category = categories[-1]['name'] if categories else None

    assets = p.get('assets', [])
    image_url = None
    if assets:
        image_url = make_image_url(assets[0], p.get('urlSlugText', ''))

    quantity = p.get('sellingSize') or None
    unit = p.get('quantityUnit') or None

    return {
        'id': f'{SOURCE}_{p["sku"]}',
        'source': SOURCE,
        'name': p.get('name', '').strip(),
        'price_chf': 0,
        'quantity': quantity,
        'unit': unit,
        'price_per_unit_chf': 0,
        'per_unit': per_unit,
        'image_url': image_url,
        'category': category,
        'price_eur': price_eur,
        'price_per_unit_eur': price_per_unit_eur,
    }

def ingest_aldi():
    print('Fetching categories...')
    categories = get_categories()
    print(f'  Found {len(categories)} subcategories')

    init_db()
    conn = get_connection()
    total = 0

    for cat in categories:
        print(f'  Fetching "{cat["name"]}" ({cat["count"]} products)...')
        products = fetch_category_products(cat['id'])
        mapped = 0
        for p in products:
            row = map_product(p)
            if row:
                insert_product(conn, row)
                mapped += 1
        conn.commit()
        total += mapped
        print(f'    Got {len(products)} raw, {mapped} mapped (total: {total})')
        time.sleep(0.3)

    conn.close()
    print(f'\nDone! {total} products ingested from ALDI SÜD')
    return total

if __name__ == '__main__':
    ingest_aldi()
