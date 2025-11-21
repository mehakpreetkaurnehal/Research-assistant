# retrieval/search_full.py

import sqlite3
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import json

DB_PATH          = "data/storage/metadata_full.db"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K            = 5

def load_chunks(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c    = conn.cursor()
    c.execute("SELECT id, paper_id, chunk_index, chunk_text, metadata FROM chunks")
    rows = c.fetchall()
    conn.close()
    chunks = []
    for r in rows:
        chunks.append({
            "id":         r[0],
            "paper_id":   r[1],
            "chunk_index":r[2],
            "chunk_text": r[3],
            "metadata":   json.loads(r[4]) if r[4] else {}
        })
    return chunks

def main():
    model  = SentenceTransformer(EMBED_MODEL_NAME)
    chunks = load_chunks()
    print("Loaded", len(chunks), "chunks")

    while True:
        query = input("\nEnter your question (or ‘exit’): ").strip()
        if query.lower() == "exit":
            break
        q_emb  = model.encode([query], show_progress_bar=False)
        q_emb  = np.array(q_emb, dtype="float32")

        # Compute cosine similarity manually
        sims = [ (c, np.dot(q_emb, model.encode([c["chunk_text"]])[0]) ) for c in chunks ]
        sims = sorted(sims, key=lambda x: x[1], reverse=True)
        top  = sims[:TOP_K]
        print("Top results:")
        for item, score in top:
            print(f"{item['paper_id']} (chunk {item['chunk_index']}): {item['chunk_text'][:200]}… – score {score:.4f}")

if __name__ == "__main__":
    main()
