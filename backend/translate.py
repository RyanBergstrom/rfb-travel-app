import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from database import get_connection, init_db

def translate_batch(texts, translation):
    results = []
    for t in texts:
        try:
            results.append(translation.translate(t))
        except Exception as e:
            print(f'    Error translating "{t}": {e}')
            results.append(t)
    return results

def translate_aldi():
    print('Adding translation columns...')
    init_db()

    conn = get_connection()

    rows = conn.execute(
        "SELECT id, name, category FROM products WHERE source = 'aldi' AND (name_en IS NULL OR name_en = '')"
    ).fetchall()
    print(f'Products to translate: {len(rows)}')

    if not rows:
        conn.close()
        print('Nothing to translate.')
        return

    print('Loading translation model...')
    import argostranslate.translate
    translation = argostranslate.translate.get_translation_from_codes('de', 'en')
    print('Model loaded.')

    BATCH = 50
    total = len(rows)
    done = 0

    for i in range(0, total, BATCH):
        batch = rows[i:i + BATCH]
        names = [r[1] for r in batch]
        cats = [r[2] for r in batch]

        name_translations = translate_batch(names, translation)
        cat_translations = translate_batch(cats, translation)

        for j, row in enumerate(batch):
            pid = row[0]
            name_en = name_translations[j]
            cat_en = cat_translations[j]
            conn.execute(
                'UPDATE products SET name_en = ?, category_en = ? WHERE id = ?',
                (name_en, cat_en, pid)
            )

        conn.commit()
        done += len(batch)
        print(f'  {done}/{total} ({done * 100 // total}%)')
        time.sleep(0.1)

    conn.close()
    print(f'Done! Translated {total} products.')

if __name__ == '__main__':
    translate_aldi()
