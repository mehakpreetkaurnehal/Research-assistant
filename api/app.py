# api/app.py
# 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
from fastapi import FastAPI
from pydantic import BaseModel
import retrieval.search as search_module  # your retrieval code
import os
from generation.generate import llm_generate

# Model for request body
class QueryRequest(BaseModel):
    question: str

# Model for response body
class QueryResponse(BaseModel):
    answer: str
    sources: list  # list of metadata for chunks/papers

app = FastAPI()

@app.post("/ask", response_model=QueryResponse)
def ask_question(req: QueryRequest):
    question = req.question
    # 1. Retrieve relevant chunks
    chunks = search_module.hybrid_search(question, search_module.load_all_chunks())
    # 2. Build prompt context
    context = "\n\n".join([c["chunk"] for c in chunks])
    prompt = f"""You are a research assistant. Use the context below to answer the question.

Context:
{context}

Question:
{question}

Answer and provide citations (paper IDs/titles)."""
    # 3. Call LLM API (example stub)
    # In production you’d call e.g. OpenAI, here we simulate
    # answer = fake_llm_call(prompt)
    answer = llm_generate(prompt)
    # 4. Construct sources list
    sources = [{"paper_id": c["paper_id"], "chunk_id": c["id"]} for c in chunks]
    return QueryResponse(answer=answer, sources=sources)

# def fake_llm_call(prompt: str) -> str:
#     # Placeholder: replace with real LLM API call
#     return "This is a placeholder answer based on the given context."

