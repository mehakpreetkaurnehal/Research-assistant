# api/app_full.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from generation.generate import llm_generate

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Configuration
DB_PATH          = "data/storage/metadata_full.db"
FAISS_INDEX_PATH = "data/storage/faiss_index.bin"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K            = 10

# Load embedding model & index at startup
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
    pdf_url: str #added

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

    q_emb = model.encode([question], show_progress_bar=False)
    q_emb = np.array(q_emb, dtype="float32")

    D, I = faiss_index.search(q_emb, TOP_K)

    retrieved = []
    seen = set()

   
    for idx in I[0]:
        if idx < len(chunks):

            c = chunks[idx]
            pid = c["paper_id"]

            if pid not in seen:       
                seen.add(pid)
                retrieved.append(c)
    if not retrieved:
        raise HTTPException(status_code=404, detail="No relevant research paper chunks found for given query")

    # 4. Build prompt
    context = "\n\n".join([r["chunk_text"] for r in retrieved])
   
    # prompt = (
    #     "You are an expert research assistant.\n"
    #     "Write a detailed, human-like answer.\n"
    #     "Important: DO NOT list sources, citations, references, or paper IDs in your answer.\n"
    #     "I will add the sources separately.\n\n"
    #     f"Context:\n{context}\n\n"
    # f"Question: {question}\n"
    # )
   
    prompt = f"""
    You are an expert AI research assistant.

    Your job:
    - Read ALL context chunks.
    - Combine information from ALL papers.
    - Provide a long, detailed, human-like explanation.
    - Include ALL methods, steps, components, definitions, or procedures mentioned.
    - NEVER miss important points.
    - Do NOT write sources inside the answer. I will add them separately.
    VERY IMPORTANT:
    - Even if context appears small, expand the explanation using all available details.
    - Answer must be multi-paragraph and fully cover the topic.
    User Question:
    {question}
    Context:
    {context}
    Write the MOST complete explanation possible:
    """


    # 5. Call the generation function
    answer = llm_generate(prompt)

    # 6. Build sources list (one per paper)
    # sources = [{"paper_id": r["paper_id"]} for r in retrieved]
    # sources = [
    #     Source(
    #         paper_id=r["paper_id"],
    #         pdf_url=r["metadata"].get("pdf_url", "")
    #     )
    #     for r in retrieved
    # ]
    sources = [
    Source(
        paper_id=r["paper_id"],
        pdf_url=f"https://arxiv.org/pdf/{r['paper_id']}.pdf"
    )
    for r in retrieved]


    return QAResponse(answer=answer, sources=sources)














# properly working code 
# from fastapi import FastAPI
# from pydantic import BaseModel
# import sqlite3
# import json
# import os
# import numpy as np
# import faiss
# from sentence_transformers import SentenceTransformer

# # Configuration
# DB_PATH          = "data/storage/metadata_full.db"
# FAISS_INDEX_PATH = "data/storage/faiss_index.bin"
# EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# TOP_K            = 5

# # Load models & index at startup
# model = SentenceTransformer(EMBED_MODEL_NAME)
# print("Loaded embedding model:", EMBED_MODEL_NAME)

# if not os.path.exists(FAISS_INDEX_PATH):
#     raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

# faiss_index = faiss.read_index(FAISS_INDEX_PATH)
# print("Loaded FAISS index. Total vectors:", faiss_index.ntotal)

# # Load chunk metadata from DB
# conn = sqlite3.connect(DB_PATH)
# cursor = conn.cursor()
# cursor.execute("SELECT id, paper_id, chunk_index, chunk_text, metadata FROM chunks")
# rows = cursor.fetchall()
# conn.close()

# chunks = []
# for r in rows:
#     chunks.append({
#         "id":         r[0],
#         "paper_id":   r[1],
#         "chunk_index":r[2],
#         "chunk_text": r[3],
#         "metadata":   json.loads(r[4]) if r[4] else {}
#     })

# print("Loaded chunk metadata count:", len(chunks))

# # API setup
# app = FastAPI()


# class Source(BaseModel):
#     paper_id: str
    
# class QARequest(BaseModel):
#     question: str

# class QAResponse(BaseModel):
#     answer:  str
#     # sources: list
#     sources: list[Source]

# @app.post("/ask", response_model=QAResponse)
# def ask_question(req: QARequest):
#     question = req.question.strip()
#     if not question:
#         return QAResponse(answer="No question provided.", sources=[])

#     # 1. Embed the question
#     q_emb = model.encode([question], show_progress_bar=False)
#     q_emb = np.array(q_emb, dtype="float32")

#     # 2. Search on FAISS
#     D, I = faiss_index.search(q_emb, TOP_K)

#     # 3. Retrieve top chunks
#     retrieved = []
#     for idx in I[0]:
#         if idx < len(chunks):
#             retrieved.append(chunks[idx])

#     # 4. Build prompt
#     context = "\n\n".join([ r["chunk_text"] for r in retrieved ])
#     prompt  = f"""You are a helpful research assistant.
#     Use the context below to answer the question clearly, and then list the sources used.

# Context:
# {context}

# Question:
# {question}
# """

#     # 5. Call your generation function (import from your generate module)
#     from generation.generate import llm_generate
#     # answer = llm_generate(prompt, max_tokens=200)
#     answer = llm_generate(prompt)


#     # 6. Build sources list
#     # sources = [ {"paper_id": r["paper_id"], "chunk_index": r["chunk_index"]} for r in retrieved ]
#     sources = [{"paper_id": r["paper_id"]} for r in retrieved]

#     return QAResponse(answer=answer, sources=sources)










