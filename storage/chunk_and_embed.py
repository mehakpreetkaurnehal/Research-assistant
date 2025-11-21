# storage/chunk_and_embed.py

import os
import sqlite3
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Configuration
RAW_TEXT_FOLDER = "data/raw/texts"
DB_PATH = "data/storage/metadata.db"
EMBEDDING_DIM = 384  # model's embedding size
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# 2. Initialize embedding model
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# 3. Prepare storage: connect to SQLite metadata DB (for simplicity)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
# create tables if they don’t exist
c.execute('''
  CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT,
    chunk_text TEXT,
    embedding BLOB,
    metadata TEXT
  )
''')
conn.commit()

# 4. Chunking: create splitter
splitter = RecursiveCharacterTextSplitter(
  chunk_size=500,      # roughly 500 characters per chunk
  chunk_overlap=100    # overlap to retain context
)

# 5. Process each text file
for fname in tqdm(os.listdir(RAW_TEXT_FOLDER), desc="Chunking and embedding"):
    if not fname.endswith(".txt"):
        continue
    paper_id = fname.replace(".txt", "")
    filepath = os.path.join(RAW_TEXT_FOLDER, fname)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    # split into chunks
    chunks = splitter.split_text(text)
    for chunk in chunks:
        # generate embedding (vector)
        embedding = model.encode(chunk)
        # store metadata JSON
        metadata = {"paper_id": paper_id}
        # insert into DB
        c.execute(
          'INSERT INTO chunks (paper_id, chunk_text, embedding, metadata) VALUES (?, ?, ?, ?)',
          (paper_id, chunk, embedding.tobytes(), json.dumps(metadata))
        )
    conn.commit()
conn.close()
print("Chunking & embedding done.")
