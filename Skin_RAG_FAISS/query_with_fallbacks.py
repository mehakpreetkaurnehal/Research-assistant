import os
import json
import faiss
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

# =========================
# CONFIGURATION
# =========================
FAISS_INDEX_PATH = "faiss_store/chunks.index"
CHUNK_METADATA_PATH = "faiss_store/chunk_metadata.json"

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 8
MAX_CHUNK_CHARS = 450
MAX_L2_DISTANCE = 1.2

# LLM API Keys (if available)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Local Ollama REST API
OLLAMA_LOCAL_URL = "http://localhost:11434/api/generate"

# =========================
# LOAD EMBEDDING & INDEX
# =========================
print("Loading embedding model...")
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

print("Loading FAISS index...")
faiss_index = faiss.read_index(FAISS_INDEX_PATH)

print("Loading metadata...")
with open(CHUNK_METADATA_PATH, "r", encoding="utf-8") as f:
    chunk_metadata = json.load(f)

assert faiss_index.ntotal == len(chunk_metadata), "Index and metadata mismatch!"

# =========================
# RETRIEVAL
# =========================
def retrieve_chunks(query: str) -> List[dict]:
    query_emb = embed_model.encode([query]).astype("float32")
    distances, indices = faiss_index.search(query_emb, TOP_K)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if float(dist) > MAX_L2_DISTANCE:
            continue
        meta = chunk_metadata[idx]
        results.append(meta)
    return results

# =========================
# PROMPT BUILDER
# =========================
def truncate(text: str, max_chars: int) -> str:
    return text[:max_chars].rsplit(" ", 1)[0]

def build_prompt(question: str, chunks: List[dict]) -> (str, List[str]):
    context_texts = []
    urls = set()
    for c in chunks:
        snippet = truncate(c["chunk_text"], MAX_CHUNK_CHARS)
        context_texts.append(snippet)
        if "paper_url" in c:
            urls.add(c["paper_url"])

    context_body = "\n\n---\n\n".join(context_texts)

    prompt = f"""
You are a helpful research assistant.

Use ONLY the information below.
Do NOT add anything not supported by the context.

QUESTION:
{question}

CONTEXT:
{context_body}

ANSWER:
""".strip()

    return prompt, list(urls)

# =========================
# LLM CALLS
# =========================

def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key not set")
    url = "https://api.generativeai.googleapis.com/v1/assistants/text"
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    body = {"input": prompt}
    resp = requests.post(url, json=body, headers=headers, timeout=12)
    resp.raise_for_status()
    return resp.json().get("output_text", "").strip()

def call_openai(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key not set")
    import openai
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def call_mistral(prompt: str) -> str:
    if not MISTRAL_API_KEY:
        raise RuntimeError("Mistral API key not set")
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "devstral-small-2505",
        "messages": [
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    resp = requests.post(url, json=body, headers=headers, timeout=12)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def call_ollama(prompt: str) -> str:
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(OLLAMA_LOCAL_URL, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json().get("response", "").strip()

def call_llm_with_fallback(prompt: str) -> str:
    for fn in [call_gemini, call_openai, call_mistral, call_ollama]:
        try:
            answer = fn(prompt)
            if answer:
                return answer
        except Exception:
            continue
    return "❌ INSUFFICIENT MODEL AVAILABILITY"

# =========================
# MAIN
# =========================
def main():
    print("\nRAG system ready. Type 'exit' to quit.\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() == "exit":
            break

        chunks = retrieve_chunks(question)
        if not chunks:
            print("❌ No relevant context found!")
            continue

        prompt, urls = build_prompt(question, chunks)

        print("\n🌐 Generating answer...\n")
        answer = call_llm_with_fallback(prompt)

        print("\n=== ANSWER ===\n")
        print(answer)
        print("\n=== SOURCES ===\n")
        for u in urls:
            print(u)
        print("\n===================\n")

if __name__ == "__main__":
    main()
