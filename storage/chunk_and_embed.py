# storage/chunk_and_embed.py

# storage/chunk_and_embed_full.py

import os
import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm

FULLTEXT_FOLDER    = "data/raw/fulltexts"
DB_PATH            = "data/storage/metadata_full.db"
FAISS_INDEX_PATH   = "data/storage/faiss_index.bin"

EMBED_MODEL_NAME   = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE         = 1000
CHUNK_OVERLAP      = 200

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

def main():
    print("Loading embedding model:", EMBED_MODEL_NAME)
    model = SentenceTransformer(EMBED_MODEL_NAME)

    conn   = init_db()
    cursor = conn.cursor()

    faiss_index    = None
    embedding_dim  = None

    files = [f for f in os.listdir(FULLTEXT_FOLDER) if f.lower().endswith(".txt")]
    print(f"Found {len(files)} full-text files to process.")

    for fname in tqdm(files, desc="Chunking & embedding full-text"):
        paper_id = fname.replace(".txt", "")
        path     = os.path.join(FULLTEXT_FOLDER, fname)

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
            meta = {"paper_id": paper_id, "chunk_index": idx}
            cursor.execute(
                "INSERT INTO chunks (paper_id, chunk_index, chunk_text, metadata) VALUES (?, ?, ?, ?)",
                (paper_id, idx, chunk_text_content, json.dumps(meta))
            )
        conn.commit()

    if faiss_index is not None:
        save_faiss(faiss_index)
    conn.close()
    print("✔ Chunking & embedding completed.")

if __name__ == "__main__":
    main()



# correct code 

# import os
# import sqlite3
# import json
# from sentence_transformers import SentenceTransformer
# import numpy as np
# from tqdm import tqdm
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# # 1. Configuration
# RAW_TEXT_FOLDER = "data/raw/texts"
# DB_PATH = "data/storage/metadata.db"
# EMBEDDING_DIM = 384  # model's embedding size
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# # 2. Initialize embedding model
# model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# # 3. Prepare storage: connect to SQLite metadata DB (for simplicity)
# os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
# conn = sqlite3.connect(DB_PATH)
# c = conn.cursor()
# # create tables if they don’t exist
# c.execute('''
#   CREATE TABLE IF NOT EXISTS chunks (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     paper_id TEXT,
#     chunk_text TEXT,
#     embedding BLOB,
#     metadata TEXT
#   )
# ''')
# conn.commit()

# # 4. Chunking: create splitter
# splitter = RecursiveCharacterTextSplitter(
#   chunk_size=500,      # roughly 500 characters per chunk
#   chunk_overlap=100    # overlap to retain context
# )

# # 5. Process each text file
# for fname in tqdm(os.listdir(RAW_TEXT_FOLDER), desc="Chunking and embedding"):
#     if not fname.endswith(".txt"):
#         continue
#     paper_id = fname.replace(".txt", "")
#     filepath = os.path.join(RAW_TEXT_FOLDER, fname)
#     with open(filepath, "r", encoding="utf-8") as f:
#         text = f.read()
#     # split into chunks
#     chunks = splitter.split_text(text)
#     for chunk in chunks:
#         # generate embedding (vector)
#         embedding = model.encode(chunk)
#         # store metadata JSON
#         metadata = {"paper_id": paper_id}
#         # insert into DB
#         c.execute(
#           'INSERT INTO chunks (paper_id, chunk_text, embedding, metadata) VALUES (?, ?, ?, ?)',
#           (paper_id, chunk, embedding.tobytes(), json.dumps(metadata))
#         )
#     conn.commit()
# conn.close()
# print("Chunking & embedding done.")
