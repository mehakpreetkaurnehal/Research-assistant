import os
import re
import sqlite3
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH", "data_ar_pb/research.db")
FAISS_DIR = os.getenv("FAISS_DIR", "faiss_store_metadata")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))      # words
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

os.makedirs(FAISS_DIR, exist_ok=True)

FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "chunks.index")
CHUNK_META_PATH = os.path.join(FAISS_DIR, "chunk_metadata.json")

def sanitize(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip()

def is_table_line(line: str) -> bool:
    return line.startswith("<<<TABLE_")

def chunk_text_with_overlap(text: str, max_words: int, overlap: int):
    """
    Chunk text with overlap.
    Ensures tables are kept intact in a single chunk.
    """
    words = text.split()
    chunks = []
    i = 0

    while i < len(words):
        # Table-safe handling
        if is_table_line(words[i]):
            table_block = []
            while i < len(words) and not is_table_line(words[i]):
                table_block.append(words[i])
                i += 1
            chunks.append(" ".join(table_block))
            continue

        end = min(i + max_words, len(words))
        chunk_words = words[i:end]
        chunks.append(" ".join(chunk_words))
        i += max_words - overlap

    return chunks


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
SELECT pm.id, pm.paper_id, pm.url, pm.title, pm.authors, pm.journal, pm.pub_date, pf.full_text
FROM papers_metadata pm
JOIN papers_fulltext pf ON pm.id = pf.metadata_id
""")

rows = cur.fetchall()
conn.close()

print(f"📄 Loaded {len(rows)} documents for embedding")

print(f"🧠 Loading embedding model: {EMBED_MODEL_NAME}")
model = SentenceTransformer(EMBED_MODEL_NAME)

faiss_index = None
chunk_metadata = []
vector_count = 0

for meta_id, paper_id, url, title, authors, journal, pub_date, full_text in tqdm(rows, desc="Chunking & embedding"):
    if not full_text:
        continue

    clean_text = sanitize(full_text)
    chunks = chunk_text_with_overlap(
        clean_text,
        max_words=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP
    )

    if not chunks:
        continue

    embeddings = model.encode(chunks, show_progress_bar=False)
    embeddings = np.array(embeddings, dtype="float32")

    if faiss_index is None:
        dim = embeddings.shape[1]
        faiss_index = faiss.IndexFlatL2(dim)

    faiss_index.add(embeddings)

    for idx, chunk in enumerate(chunks):
        # Store additional metadata for each chunk
        chunk_metadata.append({
            "paper_id": paper_id,
            "paper_url": url,
            "title": title,
            "authors": authors,
            "journal": journal,
            "pub_date": pub_date,
            "chunk_index": idx,
            "chunk_text": chunk
        })
        vector_count += 1


faiss.write_index(faiss_index, FAISS_INDEX_PATH)

with open(CHUNK_META_PATH, "w", encoding="utf-8") as f:
    json.dump(chunk_metadata, f, indent=2)

print("\n✅ FAISS indexing complete")
print(f"🔢 Total vectors: {vector_count}")
print(f"📁 FAISS index saved at: {FAISS_INDEX_PATH}")
print(f"📄 Chunk metadata saved at: {CHUNK_META_PATH}")
