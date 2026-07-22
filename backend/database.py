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
            price_chf DECIMAL(10,2) NOT NULL,
            quantity VARCHAR,
            unit VARCHAR,
            price_per_unit_chf DECIMAL(10,2),
            per_unit VARCHAR,
            image_url VARCHAR,
            category VARCHAR,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.close()

def insert_product(conn, p):
    conn.execute('''
        INSERT OR REPLACE INTO products
        (id, source, name, price_chf, quantity, unit, price_per_unit_chf, per_unit, image_url, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p['id'], p['source'], p['name'], p['price_chf'],
        p.get('quantity'), p.get('unit'), p.get('price_per_unit_chf'),
        p.get('per_unit'), p.get('image_url'), p.get('category')
    ))

def get_categories():
    conn = get_connection()
    results = conn.execute('''
        SELECT category, COUNT(*) as cnt FROM products
        GROUP BY category ORDER BY category ASC
    ''').fetchall()
    conn.close()
    return [{'category': r[0], 'count': r[1]} for r in results]

def search_products(query='', category='', limit=50):
    conn = get_connection()
    where = []
    params = []
    if query.strip():
        where.append('name ILIKE ?')
        params.append(f'%{query}%')
    if category.strip():
        where.append('category = ?')
        params.append(category)
    sql = 'SELECT id, source, name, price_chf, quantity, unit, price_per_unit_chf, per_unit, image_url, category FROM products'
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY price_chf ASC LIMIT ?'
    params.append(limit)
    results = conn.execute(sql, params).fetchall()
    conn.close()
    cols = ['id', 'source', 'name', 'price_chf', 'quantity', 'unit',
            'price_per_unit_chf', 'per_unit', 'image_url', 'category']
    return [dict(zip(cols, row)) for row in results]

def get_all_products():
    conn = get_connection()
    results = conn.execute('''
        SELECT id, source, name, price_chf, quantity, unit,
               price_per_unit_chf, per_unit, image_url, category
        FROM products ORDER BY name ASC
    ''').fetchall()
    conn.close()
    cols = ['id', 'source', 'name', 'price_chf', 'quantity', 'unit',
            'price_per_unit_chf', 'per_unit', 'image_url', 'category']
    return [dict(zip(cols, row)) for row in results]

def product_count():
    conn = get_connection()
    count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    conn.close()
    return count
