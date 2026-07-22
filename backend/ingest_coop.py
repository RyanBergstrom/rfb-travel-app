import json
import re
import html as html_mod
import os

from database import get_connection, init_db, insert_product

def _category_from_url(url):
    m = re.search(r'/en/food/([^/]+)/c/', url)
    if m:
        return m.group(1)
    return 'unknown'

def extract_products_from_har(har_path):
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)

    products = []
    source = os.path.basename(har_path).replace('.har', '')

    for entry in har['log']['entries']:
        resp = entry['response']
        content = resp.get('content', {})
        text = content.get('text', '')
        ct = content.get('mimeType', '')

        if 'text/html' not in ct or not text:
            continue

        meta_match = re.search(
            r'<meta[^>]*data-pagecontent-json=\'(.*?)\'[^>]*>', text
        )
        if meta_match:
            raw = meta_match.group(1)
            decoded = html_mod.unescape(raw)
            try:
                data = json.loads(decoded)
            except json.JSONDecodeError:
                continue

            url = entry['request']['url']
            category = _category_from_url(url)

            for anchor in data.get('anchors', []):
                if anchor.get('name') != 'productTile':
                    continue
                elements = anchor.get('json', {}).get('elements', [])
                if not isinstance(elements, list):
                    continue

                for el in elements:
                    pid = str(el.get('id', ''))
                    title = el.get('title', '')
                    price_str = el.get('price', '0')
                    currency = el.get('currency', 'CHF')
                    img = el.get('image', {})
                    img_url = img.get('src', '') if isinstance(img, dict) else ''
                    quantity = el.get('quantity', '')
                    price_context = el.get('priceContext', '')

                    if currency != 'CHF':
                        continue

                    price_chf = float(price_str) if price_str else 0.0
                    price_per_unit_chf = None
                    per_unit = None

                    if price_context:
                        parts = price_context.split('/')
                        if len(parts) == 2:
                            try:
                                price_per_unit_chf = float(parts[0])
                                per_unit = parts[1]
                            except ValueError:
                                pass

                    products.append({
                        'id': f"{source}_{pid}",
                        'source': source,
                        'name': title.strip(),
                        'price_chf': price_chf,
                        'quantity': quantity if quantity else None,
                        'unit': None,
                        'price_per_unit_chf': price_per_unit_chf,
                        'per_unit': per_unit,
                        'image_url': img_url if img_url else None,
                        'category': category,
                    })

    return products

def ingest_har(har_path):
    print(f"Ingesting {har_path}...")
    products = extract_products_from_har(har_path)
    print(f"  Found {len(products)} products")

    init_db()
    conn = get_connection()
    for p in products:
        insert_product(conn, p)
    conn.commit()
    conn.close()
    print(f"  Inserted {len(products)} products into database")
    return products

if __name__ == '__main__':
    ingest_har(os.path.join(os.path.dirname(__file__), '..', 'harfiles', 'www.coop.ch.har'))
