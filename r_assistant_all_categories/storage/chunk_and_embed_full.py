# storage/chunk_and_embed_full.py

import os
import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm
import pandas as pd

FULLTEXT_FOLDER    = "data/raw/fulltexts"
DB_PATH            = "data/storage/metadata_full.db"
FAISS_INDEX_PATH   = "data/storage/faiss_index.bin"

EMBED_MODEL_NAME   = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE         = 1000
CHUNK_OVERLAP      = 200

# Initialize DB
def init_db(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"Initializing SQLite DB at: {db_path}")
    conn = sqlite3.connect(db_path)
    c    = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id     TEXT,
            chunk_index  INTEGER,
            chunk_text   TEXT,
            metadata     TEXT
        )
    ''')
    conn.commit()
    print("Table ‘chunks’ ensured.")
    return conn

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start  = 0
    length = len(text)
    while start < length:
        end   = min(start + size, length)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == length:
            break
        start = end - overlap
    return chunks

def load_or_create_faiss(dim, index_path=FAISS_INDEX_PATH):
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    if os.path.exists(index_path):
        print("Loading existing FAISS index from:", index_path)
        index = faiss.read_index(index_path)
    else:
        print("Creating new FAISS index with dimension:", dim)
        index = faiss.IndexFlatL2(dim)
    return index

def save_faiss(index, index_path=FAISS_INDEX_PATH):
    faiss.write_index(index, index_path)
    print("Saved FAISS index to:", index_path)

def main(category: str = "cs.AI"):
    # Load embedding model
    print("Loading embedding model:", EMBED_MODEL_NAME)
    model = SentenceTransformer(EMBED_MODEL_NAME)

    # Load metadata CSV to get title/authors etc
    metadata_csv = "data/raw/arxiv_metadata.csv"
    meta_df      = pd.read_csv(metadata_csv)
    meta_map     = { row["id"]: row for _, row in meta_df.iterrows() }

    # Initialize DB
    conn   = init_db()
    cursor = conn.cursor()

    faiss_index   = None
    embedding_dim = None

    # Get list of full-text .txt files for this category
    files = [f for f in os.listdir(FULLTEXT_FOLDER) if f.lower().endswith(".txt")]
    print(f"Found {len(files)} full-text files to process for category {category}")

    for fname in tqdm(files, desc="Chunking & embedding full-text"):
        paper_id = fname.replace(".txt", "")
        if paper_id not in meta_map:
            print(f"[WARN] metadata not found for paper_id {paper_id}, skipping.")
            continue
        row      = meta_map[paper_id]
        title    = row["title"]
        authors  = row["authors"]
        published= row["published"]
        summary  = row["summary"]
        pdf_url  = row["pdf_url"]

        path = os.path.join(FULLTEXT_FOLDER, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        print(f"  => {paper_id}: {len(chunks)} chunks")

        try:
            embeddings = model.encode(chunks, show_progress_bar=False)
        except Exception as e:
            print(f"[ERROR] Embedding failed for {paper_id}: {e}")
            continue

        embeddings = np.array(embeddings, dtype="float32")

        if faiss_index is None:
            embedding_dim = embeddings.shape[1]
            faiss_index   = load_or_create_faiss(dim=embedding_dim)

        faiss_index.add(embeddings)

        for idx, chunk_text_content in enumerate(chunks):
            meta = {
                "paper_id":      paper_id,
                "chunk_index":   idx,
                "title":          title,
                "authors":        authors,
                "published":       published,
                "abstract":        summary,
                "pdf_url":         pdf_url,
                "category":        category
            }
            cursor.execute(
                "INSERT INTO chunks (paper_id, chunk_index, chunk_text, metadata) VALUES (?, ?, ?, ?)",
                (paper_id, idx, chunk_text_content, json.dumps(meta))
            )
        conn.commit()

    if faiss_index is not None:
        save_faiss(faiss_index)
    conn.close()
    print("✔ Chunking & embedding completed for category:", category)

if __name__ == "__main__":
    main()
