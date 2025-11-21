# api/app_full.py

from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Configuration
DB_PATH          = "data/storage/metadata_full.db"
FAISS_INDEX_PATH = "data/storage/faiss_index.bin"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K            = 5

# Load models & index at startup
model = SentenceTransformer(EMBED_MODEL_NAME)
print("Loaded embedding model:", EMBED_MODEL_NAME)

if not os.path.exists(FAISS_INDEX_PATH):
    raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

faiss_index = faiss.read_index(FAISS_INDEX_PATH)
print("Loaded FAISS index. Total vectors:", faiss_index.ntotal)

# Load chunk metadata from DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT id, paper_id, chunk_index, chunk_text, metadata FROM chunks")
rows = cursor.fetchall()
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

print("Loaded chunk metadata count:", len(chunks))

# API setup
app = FastAPI()


class Source(BaseModel):
    paper_id: str
    
class QARequest(BaseModel):
    question: str

class QAResponse(BaseModel):
    answer:  str
    # sources: list
    sources: list[Source]

@app.post("/ask", response_model=QAResponse)
def ask_question(req: QARequest):
    question = req.question.strip()
    if not question:
        return QAResponse(answer="No question provided.", sources=[])

    # 1. Embed the question
    q_emb = model.encode([question], show_progress_bar=False)
    q_emb = np.array(q_emb, dtype="float32")

    # 2. Search on FAISS
    D, I = faiss_index.search(q_emb, TOP_K)

    # 3. Retrieve top chunks
    retrieved = []
    for idx in I[0]:
        if idx < len(chunks):
            retrieved.append(chunks[idx])

    # 4. Build prompt
    context = "\n\n".join([ r["chunk_text"] for r in retrieved ])
    prompt  = f"""You are a helpful research assistant.
    Use the context below to answer the question clearly, and then list the sources used.

Context:
{context}

Question:
{question}
"""

    # 5. Call your generation function (import from your generate module)
    from generation.generate import llm_generate
    # answer = llm_generate(prompt, max_tokens=200)
    answer = llm_generate(prompt)


    # 6. Build sources list
    # sources = [ {"paper_id": r["paper_id"], "chunk_index": r["chunk_index"]} for r in retrieved ]
    sources = [{"paper_id": r["paper_id"]} for r in retrieved]

    return QAResponse(answer=answer, sources=sources)
