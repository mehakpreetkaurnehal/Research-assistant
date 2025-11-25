# api/app_full.py

from fastapi import FastAPI, HTTPException
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

# Load model & index at startup
model = SentenceTransformer(EMBED_MODEL_NAME)
print("Loaded embedding model:", EMBED_MODEL_NAME)

if not os.path.exists(FAISS_INDEX_PATH):
    raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

faiss_index = faiss.read_index(FAISS_INDEX_PATH)
print("Loaded FAISS index. Total vectors:", faiss_index.ntotal)

# Load chunk metadata from DB
conn   = sqlite3.connect(DB_PATH)
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
app = FastAPI(title="Research Paper Assistant API")

class Source(BaseModel):
    paper_id:       str
    title:          str | None = None
    authors:        list[str] | None = None
    published_date: str | None = None
    abstract:       str | None = None
    url:            str | None = None
    category:       str | None = None

class QARequest(BaseModel):
    question: str

class QAResponse(BaseModel):
    answer:  str
    sources: list[Source]

@app.post("/ask", response_model=QAResponse)
def ask_question(req: QARequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="No question provided.")

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

    if not retrieved:
        raise HTTPException(status_code=404, detail="No relevant research paper chunks found for given query.")

    # 4. Build prompt context
    context = "\n\n".join([ r["chunk_text"] for r in retrieved ])
    prompt  = f"""You are a helpful research assistant.
Use only the following research paper excerpts to answer the question. Provide a detailed explanation (several paragraphs) and then list the sources at the end. Include references with paper IDs, titles, authors, publication date, category and URL.

Context:
{context}

Question:
{question}

Answer (with references):"""

    # 5. Generation call (your LLM function)
    from generation.generate import llm_generate
    answer = llm_generate(prompt)

    # 6. Build distinct sources list (no duplicates)
    seen_papers = set()
    sources     = []
    for r in retrieved:
        meta = r["metadata"]
        pid  = meta.get("paper_id")
        if pid and (pid not in seen_papers):
            seen_papers.add(pid)
            url = meta.get("pdf_url")
            if not url:
                url = f"https://arxiv.org/pdf/{pid}"
                
            sources.append(Source(
                paper_id       = pid,
                title          = meta.get("title"),
                authors        = meta.get("authors"),
                published_date = meta.get("published"),
                abstract       = meta.get("abstract"),
                url            = url,
                category       = meta.get("category")
            ))

    return QAResponse(answer=answer, sources=sources)
