import os
from dotenv import load_dotenv
import google.generativeai as genai
from txtai import Embeddings

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)


def generate_answer(context: str, question: str) -> str:
    """
    THIS FUNCTION GENERATES THE FINAL ANSWER
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are a medical assistant.

Answer the question using ONLY the information explicitly stated
in the context below.

If the reason or explanation is NOT clearly stated in the context,
say: "The reason is not explicitly stated in the text."

Do NOT infer, assume, or speculate beyond the given context.

Context:
{context}

Question:
{question}

Answer:
"""


    response = model.generate_content(prompt)
    return response.text.strip()

def index_documents(embeddings, documents):
    print("Indexing documents...")
    embeddings.index(documents)
    print(f"Indexed {len(documents)} chunks.\n")

def run_queries(embeddings):
    print("Enter questions (type 'quit' or 'exit' to stop):")

    while True:
        question = input("\nQuery: ").strip()
        if question.lower() in ("quit", "exit"):
            print("Exiting.")
            break

        # 1️⃣ RETRIEVAL
        results = embeddings.search(question, 3)

        if not results:
            print("No relevant context found.")
            continue

        # 2️⃣ BUILD CONTEXT
        context_chunks = []

        for item in results:
            if isinstance(item, dict):
                text = item.get("text", "")
            elif isinstance(item, (tuple, list)):
                text = embeddings.get(item[0])
            else:
                continue

            if text:
                context_chunks.append(text)

        if not context_chunks:
            print("No usable context retrieved.")
            continue

        combined_context = "\n\n".join(context_chunks)

        # 3️⃣ ANSWER GENERATION
        answer = generate_answer(combined_context, question)

        print("\n================ ANSWER ================\n")
        print(answer)
        print("\n========================================\n")

def main():
    embeddings = Embeddings(
        path="neuml/pubmedbert-base-embeddings",
        content=True
    )

    # ✅ PROPERLY CHUNKED MEDICAL TEXT
    documents = [
        "On January 2017, she started to feel pain in her left hip again. "
        "Physical examination showed tenderness and a 1.5 cm shortening of the left limb.",

        "DXA examination showed bone mineral density around the prosthesis with values "
        "for areas 1–7 of 1.352, 1.041, 0.940, 2.031, 0.908, 0.889, and 1.002 g/cm2.",

        "Right femur neck BMD was 1.114 g/cm2, right hip BMD was 1.133 g/cm2, "
        "and lumbar spine (L1–4) BMD was 1.496 g/cm2.",

        "ESR was 11 mm/h and CRP was 3.11 mg/L, with no evidence of infection.",

        "She was diagnosed with aseptic prosthetic loosening.",

        "She was treated with zoledronic acid as a non-surgical management approach."
    ]

    index_documents(embeddings, documents)
    run_queries(embeddings)
if __name__ == "__main__":
    main()
