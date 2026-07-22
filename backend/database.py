import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'travel_prices.duckdb')

def get_connection():
    return duckdb.connect(DB_PATH)

def init_db():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR PRIMARY KEY,
            source VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            price_chf DECIMAL(10,2),
            quantity VARCHAR,
            unit VARCHAR,
            price_per_unit_chf DECIMAL(10,2),
            per_unit VARCHAR,
            image_url VARCHAR,
            category VARCHAR,
            price_eur DECIMAL(10,2),
            price_per_unit_eur DECIMAL(10,2),
            name_en VARCHAR,
            category_en VARCHAR,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        conn.execute('ALTER TABLE products ADD COLUMN price_eur DECIMAL(10,2)')
    except Exception:
        pass
    try:
        conn.execute('ALTER TABLE products ADD COLUMN price_per_unit_eur DECIMAL(10,2)')
    except Exception:
        pass
    try:
        conn.execute('ALTER TABLE products ADD COLUMN name_en VARCHAR')
    except Exception:
        pass
    try:
        conn.execute('ALTER TABLE products ADD COLUMN category_en VARCHAR')
    except Exception:
        pass
    conn.close()

def insert_product(conn, p):
    conn.execute('''
        INSERT OR REPLACE INTO products
        (id, source, name, price_chf, quantity, unit, price_per_unit_chf, per_unit, image_url, category, price_eur, price_per_unit_eur)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p['id'], p['source'], p['name'], p.get('price_chf'),
        p.get('quantity'), p.get('unit'), p.get('price_per_unit_chf'),
        p.get('per_unit'), p.get('image_url'), p.get('category'),
        p.get('price_eur'), p.get('price_per_unit_eur')
    ))

def get_categories(source=''):
    conn = get_connection()
    if source:
        results = conn.execute('''
            SELECT category, COUNT(*) as cnt FROM products
            WHERE source = ? AND category IS NOT NULL
            GROUP BY category ORDER BY category ASC
        ''', (source,)).fetchall()
    else:
        results = conn.execute('''
            SELECT category, COUNT(*) as cnt FROM products
            WHERE category IS NOT NULL
            GROUP BY category ORDER BY category ASC
        ''').fetchall()
    conn.close()
    return [{'category': r[0], 'count': r[1]} for r in results]

def search_products(query='', category='', source='', limit=50):
    conn = get_connection()
    where = []
    params = []
    if query.strip():
        where.append('(name ILIKE ? OR name_en ILIKE ?)')
        params.append(f'%{query}%')
        params.append(f'%{query}%')
    if category.strip():
        where.append('category = ?')
        params.append(category)
    if source.strip():
        where.append('source = ?')
        params.append(source)
    sql = 'SELECT id, source, name, price_chf, quantity, unit, price_per_unit_chf, per_unit, image_url, category, price_eur, price_per_unit_eur, name_en, category_en FROM products'
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY COALESCE(NULLIF(price_eur, 0), price_chf) ASC LIMIT ?'
    params.append(limit)
    results = conn.execute(sql, params).fetchall()
    conn.close()
    cols = ['id', 'source', 'name', 'price_chf', 'quantity', 'unit',
            'price_per_unit_chf', 'per_unit', 'image_url', 'category',
            'price_eur', 'price_per_unit_eur', 'name_en', 'category_en']
    return [dict(zip(cols, row)) for row in results]

def get_all_products():
    conn = get_connection()
    results = conn.execute('''
        SELECT id, source, name, price_chf, quantity, unit,
               price_per_unit_chf, per_unit, image_url, category,
               price_eur, price_per_unit_eur, name_en, category_en
        FROM products ORDER BY name ASC
    ''').fetchall()
    conn.close()
    cols = ['id', 'source', 'name', 'price_chf', 'quantity', 'unit',
            'price_per_unit_chf', 'per_unit', 'image_url', 'category',
            'price_eur', 'price_per_unit_eur', 'name_en', 'category_en']
    return [dict(zip(cols, row)) for row in results]

def get_sources():
    conn = get_connection()
    results = conn.execute('SELECT DISTINCT source FROM products ORDER BY source').fetchall()
    conn.close()
    return [r[0] for r in results]

def product_count():
    conn = get_connection()
    count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    conn.close()
    return count
