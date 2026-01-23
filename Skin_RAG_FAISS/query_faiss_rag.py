# import os
# import json
# import faiss
# import numpy as np
# import requests
# from typing import List
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv

# load_dotenv()

# FAISS_INDEX_PATH = "faiss_store/chunks.index"
# CHUNK_METADATA_PATH = "faiss_store/chunk_metadata.json"

# EMBED_MODEL_NAME = os.getenv(
#     "EMBED_MODEL",
#     "sentence-transformers/all-MiniLM-L6-v2"
# )

# TOP_K = int(os.getenv("TOP_K", "6"))
# MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", "4"))
# MAX_CHUNK_CHARS = int(os.getenv("MAX_CHUNK_CHARS", "450"))
# MAX_L2_DISTANCE = float(os.getenv("MAX_L2_DISTANCE", "1.3"))

# # Local LLM (Ollama)
# OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct")

# print("🔄 Loading embedding model...")
# embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# print("🔄 Loading FAISS index...")
# faiss_index = faiss.read_index(FAISS_INDEX_PATH)

# print("🔄 Loading chunk metadata...")
# with open(CHUNK_METADATA_PATH, "r", encoding="utf-8") as f:
#     chunk_metadata = json.load(f)

# assert faiss_index.ntotal == len(chunk_metadata), \
#     "❌ FAISS index and metadata size mismatch!"

# def retrieve_chunks(query: str) -> List[dict]:
#     q_emb = embed_model.encode([query]).astype("float32")

#     distances, indices = faiss_index.search(q_emb, TOP_K)
#     candidates = []

#     for dist, idx in zip(distances[0], indices[0]):
#         if dist > MAX_L2_DISTANCE:
#             continue

#         meta = chunk_metadata[idx]
#         candidates.append({
#             "paper_id": meta.get("paper_id", ""),
#             "chunk_index": meta.get("chunk_index", -1),
#             "chunk_text": meta.get("chunk_text", ""),
#             "distance": float(dist)
#         })

#     candidates.sort(key=lambda x: x["distance"])
#     return candidates[:MAX_CONTEXT_CHUNKS]



# def truncate(text: str, max_chars: int) -> str:
#     if len(text) <= max_chars:
#         return text
#     return text[:max_chars].rsplit(" ", 1)[0]

# def build_prompt(question: str, chunks: List[dict]) -> str:
#     context_blocks = []

#     for c in chunks:
#         snippet = truncate(c["chunk_text"], MAX_CHUNK_CHARS)
#         context_blocks.append(
#             f"[Paper {c['paper_id']}]\n{snippet}"
#         )

#     context = "\n\n---\n\n".join(context_blocks)

#     return f"""
# You are a scientific research assistant.

# RULES:
# - Use ONLY the information provided in the context
# - Do NOT add external knowledge
# - Do NOT speculate
# - If the context is insufficient, say so explicitly

# QUESTION:
# {question}

# CONTEXT:
# {context}

# Answer clearly and concisely, grounded strictly in the context.
# """.strip()


# def call_local_llm(prompt: str, temperature: float = 0.2) -> str:
#     payload = {
#         "model": OLLAMA_MODEL,
#         "prompt": prompt,
#         "temperature": temperature,
#         "stream": False
#     }

#     try:
#         r = requests.post(OLLAMA_URL, json=payload, timeout=300)
#         r.raise_for_status()
#         return r.json()["response"].strip()
#     except Exception as e:
#         return f"❌ Local LLM error: {e}"

# # =========================
# # VERBATIM COPY CHECK
# # =========================

# def copied_from_context(answer: str, chunks: List[dict]) -> bool:
#     for c in chunks:
#         snippet = c["chunk_text"][:150]
#         if snippet in answer:
#             return True
#     return False

# # =========================
# # MAIN LOOP
# # =========================

# def main():
#     print("\n📌 RAG system ready (LOCAL LLM). Type 'exit' to quit.\n")

#     while True:
#         q = input("❓ Question: ").strip()
#         if not q:
#             continue
#         if q.lower() == "exit":
#             break

#         retrieved = retrieve_chunks(q)
#         if not retrieved:
#             print("\n⚠️ No relevant context found.\n")
#             continue

#         print("\n🔍 Retrieved chunks:")
#         for i, r in enumerate(retrieved, 1):
#             print(f"{i}. Paper {r['paper_id']} | dist {r['distance']:.4f}")
#             print(r["chunk_text"][:300], "\n")

#         prompt = build_prompt(q, retrieved)

#         print("🧠 Generating answer...\n")
#         answer = call_local_llm(prompt)

#         if copied_from_context(answer, retrieved):
#             prompt += "\n\nRewrite the answer in your own words without copying."
#             answer = call_local_llm(prompt)

#         print("\n=== ANSWER ===\n")
#         print(answer)
#         print("\n==============================\n")

# if __name__ == "__main__":
#     main()




# this code was working well but it is showing that gemini is overloaded.

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

FAISS_INDEX_PATH = "faiss_store/chunks.index"
CHUNK_METADATA_PATH = "faiss_store/chunk_metadata.json"

EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K", "8"))
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

assert faiss_index.ntotal == len(chunk_metadata), "FAISS index and metadata size mismatch!"


from google import genai
from google.genai import types

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_CHAIN = [
    # "gemini-2.0-flash",
    # "gemini-2.0-flash-lite-001",
    "gemini-2.5-flash"
]

def _try_generate_gemini(prompt: str, model: str, max_tokens: int, temperature: float):
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
        print(f"[LLM ERROR] Model {model} failed: {e}")
    return None

def call_llm(prompt: str, max_tokens: int = 1200, temperature: float = 0.2) -> str:
    for model in MODEL_CHAIN:
        print(f"🔎 Trying Gemini model: {model}")
        text = _try_generate_gemini(prompt, model, max_tokens, temperature)
        if text:
            print(f"✅ Model succeeded: {model}")
            return text
        print(f"⚠️ Model {model} failed — trying next…")
    return "❌ ALL LLM MODELS FAILED TO GENERATE A RESPONSE."

def retrieve_chunks(query: str) -> List[dict]:
    # Compute query embedding
    q_emb = embed_model.encode([query], show_progress_bar=False).astype("float32")

    # FAISS search
    distances, indices = faiss_index.search(q_emb, TOP_K)
    candidates = []

    for dist, idx in zip(distances[0], indices[0]):
        if dist > MAX_L2_DISTANCE:
            continue

        meta = chunk_metadata[idx]
        candidates.append({
            "paper_id": meta.get("paper_id", ""),
            "chunk_index": meta.get("chunk_index", -1),
            "chunk_text": meta.get("chunk_text", ""),
            "distance": float(dist)
        })

    # Sort by smallest distance first
    candidates.sort(key=lambda x: x["distance"])
    return candidates[:MAX_CONTEXT_CHUNKS]


def truncate(text: str, max_chars: int) -> str:
    return text[:max_chars].rsplit(" ", 1)[0] if len(text) > max_chars else text

def build_prompt(question: str, chunks: List[dict]) -> str:
    context_sections = []
    for c in chunks:
        snippet = truncate(c["chunk_text"], MAX_CHUNK_CHARS)
        context_sections.append(f"[Paper {c['paper_id']}] {snippet}")

    context = "\n\n---\n\n".join(context_sections)

    prompt = f"""
You are a scientific research assistant.

Use ONLY the information in the context below.
Do NOT make up anything not supported by the context.
Do NOT include sources not present in the context.

QUESTION:
{question}

CONTEXT:
{context}
Provide a complete answer that explains both:
1) the main reason, and
2) the consequences if this requirement is not met,
using only the information in the context.

"""
    return prompt.strip()

def copied_from_context(answer: str, chunks: List[dict]) -> bool:
    for c in chunks:
        snippet = c["chunk_text"][:180]
        if snippet in answer:
            return True
    return False

def main():
    print("\n📌 RAG system ready. Type 'exit' to quit.\n")

    while True:
        q = input("❓ Question: ").strip()
        if not q:
            continue
        if q.lower() == "exit":
            break

        # Retrieve
        retrieved = retrieve_chunks(q)
        if not retrieved:
            print("\nNo relevant context found. Try a different query.\n")
            continue

        # Debug print of retrieved chunks
        print("\n🔍 Top retrieved chunks:")
        for i, r in enumerate(retrieved, 1):
            print(f"{i}. Paper {r['paper_id']} | dist {r['distance']:.4f}")
            print(r["chunk_text"][:300], "\n")

        # Build prompt
        prompt = build_prompt(q, retrieved)

        # Call LLM
        print("\n🧠 Generating answer…\n")
        answer = call_llm(prompt)

        # If the answer simply echoes chunks verbatim, retry
        if copied_from_context(answer, retrieved):
            prompt += "\nRewrite without copying any chunk text verbatim."
            answer = call_llm(prompt)

        print("\n=== ANSWER ===\n")
        print(answer.strip(), "\n")
        print("==============================\n")

if __name__ == "__main__":
    main()



# this code is providing chunks in an output

# import json
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from typing import List

# # =========================
# # CONFIG
# # =========================
# FAISS_INDEX_PATH = "faiss_store/chunks.index"
# CHUNK_METADATA_PATH = "faiss_store/chunk_metadata.json"

# EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# TOP_K = 8
# MAX_CONTEXT_CHUNKS = 4
# MAX_CHUNK_CHARS = 450
# MAX_L2_DISTANCE = 1.2   # tune for your index

# USE_LLM = True

# # =========================
# # LOAD MODELS
# # =========================
# print("🔄 Loading embedding model...")
# embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# print("🔄 Loading FAISS index...")
# faiss_index = faiss.read_index(FAISS_INDEX_PATH)

# print("🔄 Loading chunk metadata...")
# with open(CHUNK_METADATA_PATH, "r", encoding="utf-8") as f:
#     chunk_metadata = json.load(f)

# assert faiss_index.ntotal == len(chunk_metadata), \
#     "FAISS index and metadata size mismatch!"

# # =========================
# # UTILS
# # =========================
# def truncate(text: str, max_chars: int) -> str:
#     return text[:max_chars].rsplit(" ", 1)[0]

# # =========================
# # SEMANTIC SECTION SCORING
# # =========================
# SECTION_PRIOR = {
#     "Introduction": 1.1,
#     "Methods": 1.3,
#     "Results": 1.2,
#     "Discussion": 0.9,
#     "Other": 0.8
# }

# def score_chunk(distance: float, section: str) -> float:
#     """Lower is better"""
#     return distance / SECTION_PRIOR.get(section, 1.0)

# # =========================
# # RETRIEVAL
# # =========================
# def retrieve_chunks(query: str) -> List[dict]:
#     query_emb = embed_model.encode([query]).astype("float32")
#     distances, indices = faiss_index.search(query_emb, TOP_K)

#     candidates = []

#     for rank, idx in enumerate(indices[0]):
#         dist = float(distances[0][rank])
#         if dist > MAX_L2_DISTANCE:
#             continue

#         meta = chunk_metadata[idx]
#         adjusted_score = score_chunk(dist, meta.get("section", "Other"))

#         candidates.append({
#             "paper_id": meta["paper_id"],
#             "chunk_index": meta["chunk_index"],
#             "section": meta.get("section", "Other"),
#             "chunk_text": meta["chunk_text"],
#             "distance": dist,
#             "score": adjusted_score
#         })

#     # Sort by adjusted score
#     candidates.sort(key=lambda x: x["score"])
#     return candidates[:MAX_CONTEXT_CHUNKS]

# # =========================
# # PROMPT BUILDER (ANTI-CHUNK-DUMP)
# # =========================
# def build_prompt(question: str, chunks: List[dict]) -> str:
#     context_blocks = []

#     for c in chunks:
#         context_blocks.append(
#             truncate(c["chunk_text"], MAX_CHUNK_CHARS)
#         )

#     context = "\n\n---\n\n".join(context_blocks)

#     return f"""
# You are a scientific research assistant.

# STRICT RULES:
# - Use ONLY the information in the context.
# - DO NOT quote, copy, or restate the context verbatim.
# - DO NOT mention chunks, sections, or papers.
# - SYNTHESIZE the information into a clear answer.
# - If the context does not fully answer the question, reply exactly with:
#   "INSUFFICIENT CONTEXT TO ANSWER."

# Answer style:
# - 2–4 complete sentences
# - Plain text only
# - No bullet points
# - No citations

# QUESTION:
# {question}

# CONTEXT:
# {context}

# ANSWER:
# """.strip()

# # =========================
# # LLM CALL (PLACEHOLDER)
# # =========================
# def call_llm(prompt: str) -> str:
#     """
#     Replace this with:
#     - OpenAI
#     - Gemini
#     - Claude
#     - Local LLM
#     """
#     return (
#         "⚠️ LLM NOT CONNECTED\n\n"
#         "Prompt preview:\n\n"
#         + prompt[:1000]
#     )

# # =========================
# # COPY DETECTOR
# # =========================
# def copied_from_context(answer: str, chunks: List[dict]) -> bool:
#     for c in chunks:
#         snippet = c["chunk_text"][:180]
#         if snippet in answer:
#             return True
#     return False

# # =========================
# # MAIN LOOP
# # =========================
# def main():
#     print("\n✅ RAG system ready (semantic, synthesis-safe).")
#     print("Type 'exit' to quit.\n")

#     while True:
#         question = input("❓ Question: ").strip()
#         if question.lower() == "exit":
#             break

#         retrieved = retrieve_chunks(question)

#         if not retrieved:
#             print("\n❌ No reliable context found.")
#             print("INSUFFICIENT CONTEXT TO ANSWER.\n")
#             continue

#         prompt = build_prompt(question, retrieved)

#         if not USE_LLM:
#             print("\n🔍 Retrieved context only:\n")
#             for r in retrieved:
#                 print(f"[{r['section']}] {r['chunk_text'][:300]}\n")
#             continue

#         answer = call_llm(prompt)

#         # Safety retry if chunk dumping
#         if copied_from_context(answer, retrieved):
#             prompt += "\nRewrite the answer in your own words. Do not quote."
#             answer = call_llm(prompt)

#         print("\n=== ANSWER ===\n")
#         print(answer)
#         print("\n==============\n")

# if __name__ == "__main__":
#     main()



