# retrieval/search.py

import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import json

DB_PATH = "data/storage/metadata.db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K_VECTOR = 5    # how many to take from vector similarity
TOP_K_KEYWORD = 5   # how many via keyword search

# load embedding model
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def get_embedding(text):
    return model.encode(text)

def load_all_chunks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, paper_id, chunk_text, embedding, metadata FROM chunks")
    rows = c.fetchall()
    conn.close()
    chunks = []
    for row in rows:
        _id, paper_id, chunk_text, embedding_blob, metadata_json = row
        embedding = np.frombuffer(embedding_blob, dtype=np.float32)
        metadata = json.loads(metadata_json)
        chunks.append({"id": _id, "paper_id": paper_id, "chunk": chunk_text, "embedding": embedding, "metadata": metadata})
    return chunks

def vector_search(query, chunks, top_k=TOP_K_VECTOR):
    q_emb = get_embedding(query)
    # compute cosine similarities
    sims = []
    for ch in chunks:
        sim = np.dot(q_emb, ch["embedding"]) / (np.linalg.norm(q_emb) * np.linalg.norm(ch["embedding"]))
        sims.append((ch, sim))
    sims = sorted(sims, key=lambda x: x[1], reverse=True)
    top = sims[:top_k]
    return [item[0] for item in top]

def keyword_search(query, chunks, top_k=TOP_K_KEYWORD):
    # naive keyword search: simple substring matching
    results = []
    for ch in chunks:
        if query.lower() in ch["chunk"].lower():
            results.append(ch)
    return results[:top_k]

def hybrid_search(query, chunks):
    v_res = vector_search(query, chunks)
    k_res = keyword_search(query, chunks)
    # merge results (dedupe by id)
    seen = set()
    merged = []
    for ch in v_res + k_res:
        if ch["id"] not in seen:
            merged.append(ch)
            seen.add(ch["id"])
    return merged

def main():
    chunks = load_all_chunks()
    while True:
        query = input("Enter your question (or 'exit'): ")
        if query.lower() == "exit":
            break
        results = hybrid_search(query, chunks)
        print("Top results:")
        for r in results:
            print(f"Paper ID: {r['paper_id']} – Chunk ID: {r['id']}")
            print(r["chunk"])
            print("---")
if __name__ == "__main__":
    main()
