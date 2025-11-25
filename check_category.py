import sqlite3
import json

DB_PATH = "data/storage/metadata_full.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT metadata FROM chunks")
rows = cursor.fetchall()

category_counts = {}
for (meta_json,) in rows:
    try:
        meta = json.loads(meta_json)
        cat  = meta.get("category", None)
    except Exception:
        cat = None
    if cat is None:
        cat_key = "NONE"
    else:
        cat_key = cat.lower().strip().replace(" ", "_").replace("-", "_")
    category_counts[cat_key] = category_counts.get(cat_key, 0) + 1

conn.close()

print("Category → Count")
for cat_key, count in category_counts.items():
    print(f"{cat_key!r} → {count}")
