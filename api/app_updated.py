
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from generation.generate import llm_generate
from collections import defaultdict

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DB_PATH          = "data/storage/metadata_full.db"
FAISS_INDEX_PATH = "data/storage/faiss_index.bin"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K            = 45   # retrieve more chunks → richer answers


try:
    model = SentenceTransformer(EMBED_MODEL_NAME)
    print("Loaded embedding model:", EMBED_MODEL_NAME)
except Exception as e:
    print("❌ Error loading primary embedding model:", e)
    print("➡️ Falling back to default mini model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")


if not os.path.exists(FAISS_INDEX_PATH):
    raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

faiss_index = faiss.read_index(FAISS_INDEX_PATH)
print("Loaded FAISS index. Total vectors:", faiss_index.ntotal)

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


app = FastAPI()

class Source(BaseModel):
    paper_id: str
    pdf_url: str

class QARequest(BaseModel):
    question: str

class QAResponse(BaseModel):
    answer:  str
    sources: list[Source]

@app.post("/ask", response_model=QAResponse)
def ask_question(req: QARequest):

    question = req.question.strip()
    if not question:
        return QAResponse(answer="No question provided.", sources=[])

    # 1. Embed question text
    q_emb = model.encode([question], show_progress_bar=False)
    q_emb = np.array(q_emb, dtype="float32")

    # 2. Retrieve TOP_K chunks (NOT 1 per paper)
    D, I = faiss_index.search(q_emb, TOP_K)

    retrieved_chunks = []
    for idx in I[0]:
        if idx < len(chunks):
            retrieved_chunks.append(chunks[idx])

    if not retrieved_chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant research paper chunks found for given query"
        )

    # 3. Group chunks by paper ID
    grouped = defaultdict(list)
    for c in retrieved_chunks:
        grouped[c["paper_id"]].append(c)

    # 4. Merge chunks for each paper
    merged_papers = []
    for pid, chunk_list in grouped.items():
        merged_context = "\n".join([c["chunk_text"] for c in chunk_list])
        merged_papers.append({
            "paper_id": pid,
            "merged_text": merged_context,
            "metadata": chunk_list[0]["metadata"]
        })

    # 5. Build final context for LLM
    context = "\n\n---- PAPER SEPARATOR ----\n\n".join(
        [p["merged_text"] for p in merged_papers]
    )

    # 6. Strong improved prompt
    prompt = f"""
You are an expert AI research assistant.

Your job:
- Carefully read ALL merged chunks from ALL relevant papers.
- Combine information from all papers.
- Provide a long, detailed, multi-paragraph explanation.
- Include ALL methods, components, procedures, or architecture details.
- Do NOT miss important information.
- Do NOT include sources or citations in the answer.

User Question:
{question}

Context:
{context}

Write the MOST complete, human-quality explanation:
"""


    # 7. Call the LLM
    try:
        answer = llm_generate(prompt)
    except Exception as e:
        answer = f"LLM generation error: {e}"

    # 8. Build unique sources list
    sources = []
    for p in merged_papers:
        pdf_url = p["metadata"].get("pdf_url", "")
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{p['paper_id']}.pdf"

        sources.append(Source(
            paper_id=p["paper_id"],
            pdf_url=pdf_url
        ))

    return QAResponse(answer=answer, sources=sources)
