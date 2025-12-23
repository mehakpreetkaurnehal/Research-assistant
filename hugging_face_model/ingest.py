# ingest.py
import os
import io
import fitz  # PyMuPDF
from PIL import Image
import sqlite3
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# CONFIG
DB_FILE = "data/metadata.db"
FAISS_INDEX_FILE = "data/faiss.index"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Ensure data folder
os.makedirs("data", exist_ok=True)

# 1. Setup SQLite metadata DB
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_name TEXT,
    page_num INTEGER,
    item_type TEXT,   -- 'text', 'image_caption', optionally 'image'
    content TEXT,     -- for text or caption
    image_blob BLOB,  -- for raw image bytes (nullable)
    image_ext TEXT,   -- e.g. 'png' (nullable)
    image_index INTEGER  -- index of image on page if applicable
)
""")
conn.commit()

# 2. Embedding model
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def embed_text(text: str):
    vec = embed_model.encode(text, convert_to_numpy=True)
    return vec.astype(np.float32)

def ingest_pdf(pdf_path: str):
    pdf_name = os.path.basename(pdf_path)
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text().strip()
        if text:
            cur.execute(
                "INSERT INTO items (pdf_name, page_num, item_type, content) VALUES (?, ?, ?, ?)",
                (pdf_name, page_num, "text", text)
            )
        images = page.get_images(full=True)
        for img_i, img in enumerate(images):
            xref = img[0]
            img_dict = doc.extract_image(xref)
            img_bytes = img_dict["image"]
            ext = img_dict.get("ext", "png")
            # save image blob (optional; you could skip or write to file)
            cur.execute(
                "INSERT INTO items (pdf_name, page_num, item_type, image_blob, image_ext, image_index) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (pdf_name, page_num, "image", img_bytes, ext, img_i)
            )
        # Optionally: capture captions or figure labels if part of page text
        # (Better logic needed to align captions with images.)

    conn.commit()
    doc.close()

def build_faiss_index():
    # Read all text / caption contents (skip raw images for now)
    cur.execute("SELECT id, content FROM items WHERE item_type IN ('text','image_caption')")
    rows = cur.fetchall()
    ids = []
    vecs = []
    for r in rows:
        _id, content = r
        vec = embed_text(content)
        ids.append(_id)
        vecs.append(vec)
    if not vecs:
        print("No text to index.")
        return None
    vecs_np = np.stack(vecs)
    dim = vecs_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index = faiss.IndexIDMap(index)
    index.add_with_ids(vecs_np, np.array(ids))
    # Save index
    faiss.write_index(index, FAISS_INDEX_FILE)
    print("FAISS index built with", len(ids), "items.")
    return index

def load_faiss_index():
    if not os.path.exists(FAISS_INDEX_FILE):
        return None
    index = faiss.read_index(FAISS_INDEX_FILE)
    return index
