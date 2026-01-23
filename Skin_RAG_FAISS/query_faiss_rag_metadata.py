# # jan 21: giving better responses than FAISS only
# # code 1
# import os
# import json
# import faiss
# import numpy as np
# from typing import List
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv

# # Load environment
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise RuntimeError("Missing GEMINI_API_KEY in .env")

# FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_store_metadata/chunks.index")
# CHUNK_METADATA_PATH = os.getenv("CHUNK_METADATA_PATH", "faiss_store_metadata/chunk_metadata.json")

# EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
# TOP_K = int(os.getenv("TOP_K", "30"))
# MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))
# MAX_CHUNK_CHARS = int(os.getenv("MAX_CHUNK_CHARS", "450"))
# MAX_L2_DISTANCE = float(os.getenv("MAX_L2_DISTANCE", "1.5"))

# print("🔄 Loading embedding model...")
# embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# print("🔄 Loading FAISS index...")
# faiss_index = faiss.read_index(FAISS_INDEX_PATH)

# print("🔄 Loading chunk metadata...")
# with open(CHUNK_METADATA_PATH, "r", encoding="utf-8") as f:
#     chunk_metadata = json.load(f)

# assert faiss_index.ntotal == len(chunk_metadata), "FAISS index and metadata size mismatch!"

# # Gemini setup
# from google import genai
# from google.genai import types
# gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# MODEL_CHAIN = ["gemini-2.5-flash"]

# def _try_generate_gemini(prompt: str, model: str, max_tokens: int, temperature: float):
#     try:
#         config = types.GenerateContentConfig(
#             max_output_tokens=max_tokens,
#             temperature=temperature,
#         )
#         response = gemini_client.models.generate_content(
#             model=model,
#             contents=prompt,
#             config=config
#         )
#         if response and response.text:
#             return response.text.strip()
#     except Exception as e:
#         print(f"[LLM ERROR] {model} failed: {e}")
#     return None

# def call_llm(prompt: str, max_tokens: int = 1200, temperature: float = 0.2) -> str:
#     for model in MODEL_CHAIN:
#         print(f"🔎 Trying Gemini model: {model}")
#         text = _try_generate_gemini(prompt, model, max_tokens, temperature)
#         if text:
#             print(f"✅ Model succeeded: {model}")
#             return text
#     return "❌ ALL LLM MODELS FAILED TO GENERATE A RESPONSE."


# def retrieve_chunks(query: str) -> List[dict]:
#     # 1) Compute embedding
#     q_emb = embed_model.encode([query], show_progress_bar=False).astype("float32")

#     # 2) FAISS search
#     distances, indices = faiss_index.search(q_emb, TOP_K)
#     candidates = []

#     for dist, idx in zip(distances[0], indices[0]):
#         if dist > MAX_L2_DISTANCE:
#             continue

#         meta = chunk_metadata[idx]
#         score = 1.0 / (1.0 + dist)  # convert to intuitive relevance

#         candidates.append({
#             "paper_id": meta["paper_id"],
#             "paper_url": meta["paper_url"],
#             "title": meta["title"],
#             "authors": meta["authors"],
#             "journal": meta["journal"],
#             "pub_date": meta["pub_date"],
#             "chunk_index": meta["chunk_index"],
#             "chunk_text": meta["chunk_text"],
#             "distance": float(dist),
#             "score": float(score)
#         })

#     # sort by smallest distance first
#     candidates.sort(key=lambda x: x["distance"])
#     return candidates[:MAX_CONTEXT_CHUNKS]

# # Optional BM25 hybrid retrieval (simple Python)
# try:
#     from rank_bm25 import BM25Okapi
#     bm25 = None
#     tokenized_chunks = [c["chunk_text"].split() for c in chunk_metadata]
#     bm25 = BM25Okapi(tokenized_chunks)
#     def bm25_scores_for_query(q):
#         q_tokens = q.split()
#         return bm25.get_scores(q_tokens)
#     print("⚡ BM25 available for hybrid retrieval")
# except ImportError:
#     bm25 = None
#     print("⚠ rank_bm25 not installed — hybrid BM25 disabled")

# def hybrid_retrieve(query: str):
#     # FAISS
#     dense = retrieve_chunks(query)
#     if bm25:
#         # BM25 scoring
#         bm25_scores = bm25_scores_for_query(query)
#         for item in dense:
#             idx = item["chunk_index"]
#             item["bm25_score"] = float(bm25_scores[idx])
#             # combine dense + BM25
#             item["hybrid_score"] = item["score"] * 0.6 + item["bm25_score"] * 0.4
#         # sort by hybrid score
#         dense.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
#     return dense

# def truncate(text: str, max_chars: int) -> str:
#     return text[:max_chars].rsplit(" ", 1)[0] if len(text) > max_chars else text

# def build_prompt(question: str, chunks: List[dict]) -> str:
#     context_sections = []
#     for c in chunks:
#         snippet = truncate(c["chunk_text"], MAX_CHUNK_CHARS)
#         context_sections.append(
#             f"[Paper: {c['title']} ({c['pub_date']}) | URL: {c['paper_url']}]\n"
#             f"{snippet}\n"
#             f"(Score: {c.get('score',0):.3f}"
#             f"{' BM25:' + str(round(c.get('bm25_score',0),3)) if 'bm25_score' in c else ''})"
#         )
#     context = "\n\n---\n\n".join(context_sections)

#     prompt = f"""
# Use ONLY the context below. Do NOT invent facts.
# INCLUDE source URLs with each finding.

# QUESTION:
# {question}

# CONTEXT:
# {context}

# Provide a complete answer with citations using the provided URLs.
# """
#     return prompt.strip()

# # ---------------------------------------------------------
# def main():
#     print("\n📌 RAG system ready. Type 'exit' to quit.\n")
#     while True:
#         q = input("❓ Question: ").strip()
#         if not q:
#             continue
#         if q.lower() == "exit":
#             break

#         # retrieve (hybrid if BM25 available)
#         retrieved = hybrid_retrieve(q)
#         if not retrieved:
#             print("No relevant context found.\n")
#             continue

#         print("\n🔍 Retrieved chunks:")
#         for i, r in enumerate(retrieved, 1):
#             print(f"{i}. {r['title']} | dist {r['distance']:.4f} | score {r.get('score',0):.3f}")
#             print(f"URL: {r['paper_url']}\n")

#         prompt = build_prompt(q, retrieved)
#         print("\n🧠 Generating answer…")
#         answer = call_llm(prompt)

#         print("\n=== ANSWER ===\n")
#         print(answer.strip(), "\n")
#         print("==============================\n")

# if __name__ == "__main__":
#     main()




# jan 22, 2026: working well but answer is half generated overall better 

# import os
# import json
# import faiss
# import numpy as np
# from typing import List
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv

# # Load environment
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise RuntimeError("Missing GEMINI_API_KEY in .env")

# FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_store_metadata/chunks.index")
# CHUNK_METADATA_PATH = os.getenv("CHUNK_METADATA_PATH", "faiss_store_metadata/chunk_metadata.json")

# EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
# TOP_K = int(os.getenv("TOP_K", "30"))
# MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))
# MAX_CHUNK_CHARS = int(os.getenv("MAX_CHUNK_CHARS", "450"))
# MAX_L2_DISTANCE = float(os.getenv("MAX_L2_DISTANCE", "1.5"))

# print("🔄 Loading embedding model...")
# embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# print("🔄 Loading FAISS index...")
# faiss_index = faiss.read_index(FAISS_INDEX_PATH)

# print("🔄 Loading chunk metadata...")
# with open(CHUNK_METADATA_PATH, "r", encoding="utf-8") as f:
#     chunk_metadata = json.load(f)

# assert faiss_index.ntotal == len(chunk_metadata), "FAISS index and metadata size mismatch!"

# # Gemini setup
# from google import genai
# from google.genai import types
# gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# MODEL_CHAIN = ["gemini-2.5-flash"]

# def _try_generate_gemini(prompt: str, model: str, max_tokens: int, temperature: float):
#     try:
#         config = types.GenerateContentConfig(
#             max_output_tokens=max_tokens,
#             temperature=temperature,
#         )
#         response = gemini_client.models.generate_content(
#             model=model,
#             contents=prompt,
#             config=config
#         )
#         if response and response.text:
#             return response.text.strip()
#     except Exception as e:
#         print(f"[LLM ERROR] {model} failed: {e}")
#     return None

# def call_llm(prompt: str, max_tokens: int = 1200, temperature: float = 0.2) -> str:
#     for model in MODEL_CHAIN:
#         print(f"🔎 Trying Gemini model: {model}")
#         text = _try_generate_gemini(prompt, model, max_tokens, temperature)
#         if text:
#             print(f"✅ Model succeeded: {model}")
#             return text
#     return "❌ ALL LLM MODELS FAILED TO GENERATE A RESPONSE."


# def retrieve_chunks(query: str) -> List[dict]:
#     # 1) Compute embedding
#     q_emb = embed_model.encode([query], show_progress_bar=False).astype("float32")

#     # 2) FAISS search
#     distances, indices = faiss_index.search(q_emb, TOP_K)
#     candidates = []

#     for dist, idx in zip(distances[0], indices[0]):
#         if dist > MAX_L2_DISTANCE:
#             continue

#         meta = chunk_metadata[idx]
#         score = 1.0 / (1.0 + dist)  # convert to intuitive relevance

#         candidates.append({
#             "paper_id": meta["paper_id"],
#             "paper_url": meta["paper_url"],
#             "title": meta["title"],
#             "authors": meta["authors"],
#             "journal": meta["journal"],
#             "pub_date": meta["pub_date"],
#             "chunk_index": meta["chunk_index"],
#             "chunk_text": meta["chunk_text"],
#             "distance": float(dist),
#             "score": float(score)
#         })

#     # sort by smallest distance first
#     candidates.sort(key=lambda x: x["distance"])
#     return candidates[:MAX_CONTEXT_CHUNKS]

# # Optional BM25 hybrid retrieval (simple Python)
# try:
#     from rank_bm25 import BM25Okapi
#     bm25 = None
#     tokenized_chunks = [c["chunk_text"].split() for c in chunk_metadata]
#     bm25 = BM25Okapi(tokenized_chunks)
#     def bm25_scores_for_query(q):
#         q_tokens = q.split()
#         return bm25.get_scores(q_tokens)
#     print("⚡ BM25 available for hybrid retrieval")
# except ImportError:
#     bm25 = None
#     print("⚠ rank_bm25 not installed — hybrid BM25 disabled")

# def hybrid_retrieve(query: str):
#     # FAISS
#     dense = retrieve_chunks(query)
#     if bm25:
#         # BM25 scoring
#         bm25_scores = bm25_scores_for_query(query)
#         for item in dense:
#             idx = item["chunk_index"]
#             item["bm25_score"] = float(bm25_scores[idx])
#             # combine dense + BM25
#             item["hybrid_score"] = item["score"] * 0.6 + item["bm25_score"] * 0.4
#         # sort by hybrid score
#         dense.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
#     return dense

# def truncate(text: str, max_chars: int) -> str:
#     return text[:max_chars].rsplit(" ", 1)[0] if len(text) > max_chars else text

# def build_prompt(question: str, chunks: List[dict]) -> str:
#     context_sections = []
#     for c in chunks:
#         snippet = truncate(c["chunk_text"], MAX_CHUNK_CHARS)
#         context_sections.append(
#             f"[Paper: {c['title']} ({c['pub_date']}) | URL: {c['paper_url']}]\n"
#             f"{snippet}\n"
#             f"(Score: {c.get('score',0):.3f}"
#             f"{' BM25:' + str(round(c.get('bm25_score',0),3)) if 'bm25_score' in c else ''})"
#         )
#     context = "\n\n---\n\n".join(context_sections)

#     prompt = f"""
# Use ONLY the context below. Do NOT invent facts.
# INCLUDE source URLs with each finding.

# QUESTION:
# {question}

# CONTEXT:
# {context}

# Provide a complete answer with citations using the provided URLs.
# """
#     return prompt.strip()

# # ---------------------------------------------------------
# def main():
#     print("\n📌 RAG system ready. Type 'exit' to quit.\n")
#     while True:
#         q = input("❓ Question: ").strip()
#         if not q:
#             continue
#         if q.lower() == "exit":
#             break

#         # retrieve (hybrid if BM25 available)
#         retrieved = hybrid_retrieve(q)
#         if not retrieved:
#             print("No relevant context found.\n")
#             continue

#         print("\n🔍 Retrieved chunks:")
#         for i, r in enumerate(retrieved, 1):
#             print(f"{i}. {r['title']} | dist {r['distance']:.4f} | score {r.get('score',0):.3f}")
#             print(f"URL: {r['paper_url']}\n")

#         prompt = build_prompt(q, retrieved)
#         print("\n🧠 Generating answer…")
#         answer = call_llm(prompt)

#         print("\n=== ANSWER ===\n")
#         print(answer.strip(), "\n")
#         print("==============================\n")

# if __name__ == "__main__":
#     main()



import os
import json
import faiss
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_store_metadata/chunks.index")
CHUNK_METADATA_PATH = os.getenv("CHUNK_METADATA_PATH", "faiss_store_metadata/chunk_metadata.json")

EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K", "30"))
MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))
MAX_CHUNK_CHARS = int(os.getenv("MAX_CHUNK_CHARS", "450"))
MAX_L2_DISTANCE = float(os.getenv("MAX_L2_DISTANCE", "1.5"))

print("🔄 Loading embedding model...")
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

print("🔄 Loading FAISS index...")
faiss_index = faiss.read_index(FAISS_INDEX_PATH)

print("🔄 Loading chunk metadata...")
with open(CHUNK_METADATA_PATH, "r", encoding="utf-8") as f:
    chunk_metadata = json.load(f)

assert faiss_index.ntotal == len(chunk_metadata)

from google import genai
from google.genai import types
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_CHAIN = ["gemini-2.5-flash"]

def call_llm(prompt: str, max_tokens=1200, temperature=0.2) -> str:
    for model in MODEL_CHAIN:
        try:
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            response = gemini_client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[LLM ERROR] {model}: {e}")
    return "❌ LLM generation failed."

def retrieve_chunks(query: str) -> List[dict]:
    q_emb = embed_model.encode([query], show_progress_bar=False).astype("float32")
    distances, indices = faiss_index.search(q_emb, TOP_K)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if dist > MAX_L2_DISTANCE:
            continue
        meta = chunk_metadata[idx]
        results.append({
            **meta,
            "distance": float(dist),
            "score": 1 / (1 + dist)
        })

    results.sort(key=lambda x: x["distance"])
    return results[:MAX_CONTEXT_CHUNKS]

def truncate(text, n):
    return text[:n].rsplit(" ", 1)[0] if len(text) > n else text

def build_prompt(question: str, chunks: List[dict]) -> str:
    context = "\n\n---\n\n".join(
        truncate(c["chunk_text"], MAX_CHUNK_CHARS) for c in chunks
    )
    return f"""
Use ONLY the context below. Do NOT invent facts.

QUESTION:
{question}

CONTEXT:
{context}

Provide a clear, complete answer.
""".strip()

def build_judge_prompt(question: str, answer: str, chunks: List[dict]) -> str:
    context = "\n\n---\n\n".join(
        truncate(c["chunk_text"], 300) for c in chunks
    )
    return f"""
You are a strict scientific reviewer.

QUESTION:
{question}

CONTEXT:
{context}

GENERATED ANSWER:
{answer}

Evaluate the answer using ONLY the context.

Return your evaluation in this format:
- Grounded in context (Yes/No):
- Hallucinated statements (Yes/No + short note):
- Completeness (High/Medium/Low):
- Overclaiming (Yes/No):
- Overall quality score (1–5):
- One-line justification:
""".strip()

def judge_answer(question: str, answer: str, chunks: List[dict]) -> str:
    judge_prompt = build_judge_prompt(question, answer, chunks)
    return call_llm(judge_prompt, max_tokens=900, temperature=0.0)

def main():
    print("\n📌 RAG system ready. Type 'exit' to quit.\n")

    while True:
        q = input("❓ Question: ").strip()
        if q.lower() == "exit":
            break

        chunks = retrieve_chunks(q)
        if not chunks:
            print("No relevant context found.\n")
            continue

        prompt = build_prompt(q, chunks)
        print("\n🧠 Generating answer…")
        answer = call_llm(prompt)

        print("\n=== ANSWER ===\n")
        print(answer)

        # 🔍 Judge step
        print("\n🧪 Running LLM-as-a-Judge…")
        judgment = judge_answer(q, answer, chunks)

        print("\n=== JUDGE REPORT ===\n")
        print(judgment)
        print("==============================\n")

if __name__ == "__main__":
    main()
