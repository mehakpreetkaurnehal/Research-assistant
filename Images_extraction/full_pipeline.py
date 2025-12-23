# full_pipeline_rag_retry.py

import os
import io
import time
import sqlite3
import fitz
from PIL import Image
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv
from pathlib import Path
from google import genai
from google.genai import types

# Load env
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# Config
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")
client = genai.Client(api_key=API_KEY)

IMAGE_MODEL = "gemini-2.5-flash"
TEXT_MODEL = "gemini-2.5-flash"

EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
DB_FILE = "papers_metadata.db"
INDEX_FILE = "papers_embeddings.faiss"

MAX_IMG_RETRIES = 5
BACKOFF_INITIAL = 1  # seconds

# Setup DB
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pdf_name TEXT,
  page_num INTEGER,
  item_type TEXT,
  content TEXT
)
""")
conn.commit()

def embed_text(t):
    return EMBED_MODEL.encode(t, convert_to_numpy=True).astype(np.float32)

def image_to_text(png_bytes):
    backoff = BACKOFF_INITIAL
    for i in range(MAX_IMG_RETRIES):
        try:
            resp = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=[
                    types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
                    "Summarize this image in 2–3 short paragraphs covering all important information clearly and completely."
                ]
            )
            txt = resp.text or resp.candidates[0].content.parts[0].text
            return txt.strip()
        except Exception as e:
            print(f"[image-to-text] attempt {i+1} failed: {e}")
            time.sleep(backoff)
            backoff *= 2
    print("Skipping this image after retries.")
    return None

def ingest_pdf(pdf_path):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    pdf_name = os.path.basename(pdf_path)
    doc = fitz.open(pdf_path)
    for p in range(len(doc)):
        page = doc.load_page(p)
        txt = page.get_text().strip()
        if txt:
            cur.execute("INSERT INTO items(pdf_name,page_num,item_type,content) VALUES (?,?,?,?)",
                        (pdf_name, p, "text", txt))
        for img in page.get_images(full=True):
            xref = img[0]
            d = doc.extract_image(xref)
            img_bytes = d.get("image")
            try:
                pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                buf = io.BytesIO()
                pil.save(buf, format="PNG")
                png = buf.getvalue()
            except Exception as e:
                print("Image decode error:", e)
                continue
            desc = image_to_text(png)
            if desc:
                cur.execute("INSERT INTO items(pdf_name,page_num,item_type,content) VALUES (?,?,?,?)",
                            (pdf_name, p, "image_desc", desc))
    conn.commit()
    doc.close()
    print("Ingestion done:", pdf_name)

def build_index():
    cur.execute("SELECT id, content FROM items")
    rows = cur.fetchall()
    if not rows:
        print("No items to index")
        return None
    ids = [r[0] for r in rows]
    vecs = [embed_text(r[1]) for r in rows]
    X = np.stack(vecs)
    dim = X.shape[1]
    idx = faiss.IndexFlatL2(dim)
    idx = faiss.IndexIDMap(idx)
    idx.add_with_ids(X, np.array(ids))
    faiss.write_index(idx, INDEX_FILE)
    print("Index built:", len(ids))
    return idx

def load_index():
    if not os.path.exists(INDEX_FILE):
        return None
    return faiss.read_index(INDEX_FILE)

def retrieve(question, top_k=5):
    idx = load_index()
    if idx is None:
        raise RuntimeError("Index missing")
    qv = embed_text(question).reshape(1, -1)
    D, I = idx.search(qv, top_k)
    out = []
    for dist, iid in zip(D[0], I[0]):
        if iid < 0: continue
        cur.execute("SELECT pdf_name, page_num, item_type, content FROM items WHERE id=?", (int(iid),))
        row = cur.fetchone()
        if row:
            out.append({"pdf": row[0], "page": row[1], "type": row[2], "content": row[3], "score": float(dist)})
    return out

# def generate_answer(question, chunks):
#     context = "\n\n".join([f"Page {c['page']} ({c['type']}): {c['content']}" for c in chunks])
#     prompt = f"""You are a helpful research assistant. Use the following context to answer the question. If context isn't enough, say you don't know.

# Context:
# {context}

# Question: {question}

# Answer:"""
#     # First attempt
#     resp = client.models.generate_content(model=TEXT_MODEL, contents=[types.Part.from_text(prompt)])
#     ans = resp.text or resp.candidates[0].content.parts[0].text
#     # If truncated or seems incomplete, ask to continue
#     # Simple heuristic: if answer ends mid-sentence or length low, you may retry
#     # For simplicity, here we just return what we get
#     return ans.strip()

def generate_answer(question, chunks):
    context = "\n\n".join([f"Page {c['page']} ({c['type']}): {c['content']}" for c in chunks])
    prompt = f"""You are a helpful research assistant. Use the following context to answer the question. If context isn't enough, say you don't know.

Context:
{context}

Question: {question}

Answer:"""

    # Corrected call — pass prompt as plain string
    resp = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    ans = resp.text or resp.candidates[0].content.parts[0].text
    return ans.strip()

if __name__ == "__main__":
    pdf_path = r"D:\Project\research_assistant\Images_extraction\2511.20592v1.pdf"
    ingest_pdf(pdf_path)
    build_index()
    while True:
        q = input("Enter question (or 'exit'): ")
        if q.strip().lower() in ("exit","quit"):
            break
        chunks = retrieve(q, top_k=5)
        if not chunks:
            print("No relevant content found.")
            continue
        answer = generate_answer(q, chunks)
        print("\n--- Answer ---\n")
        print(answer)
        print("\n--- Source chunks: ---")
        for c in chunks:
            print(f"[{c['type']}] p {c['page']}, score {c['score']:.3f}")
