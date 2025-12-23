import streamlit as st
import sqlite3
import faiss
import numpy as np
import torch

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoProcessor, AutoModel
from dotenv import load_dotenv
import os

ROOT_DIR = os.path.abspath(os.path.join(os.getcwd(), ".."))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(ENV_PATH)

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

# BASE = r"D:\Project\research_assistant\r_assistant_all_categories"
DB_PATH = "data/storage/metadata.db"
TEXT_FAISS_PATH ="data/storage/text_faiss.bin"
IMG_FAISS_PATH  ="data/storage/image_faiss.bin"

TEXT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
IMAGE_MODEL_NAME = "laion/CLIP-ViT-B-32-laion2B-s34B-b79K"
LLM_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

TOP_K = 3

@st.cache_resource
def load_models():

    text_model = SentenceTransformer(TEXT_MODEL_NAME, use_auth_token=HF_TOKEN)

    img_model = AutoModel.from_pretrained(IMAGE_MODEL_NAME, token=HF_TOKEN).to("cpu")
    img_proc  = AutoProcessor.from_pretrained(IMAGE_MODEL_NAME, token=HF_TOKEN)

    tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL, token=HF_TOKEN)
    llm = AutoModelForCausalLM.from_pretrained(LLM_MODEL, token=HF_TOKEN).to("cpu")

    return text_model, img_model, img_proc, tokenizer, llm


def answer_llm(context, question, tokenizer, llm):

    prompt = f"""
Use ONLY the context from the PDF.
CONTEXT:
{context}
QUESTION:
{question}
ANSWER:
"""

    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        out = llm.generate(**inputs, max_new_tokens=300)

    return tokenizer.decode(out[0], skip_special_tokens=True)

def main():

    st.title("📘 Multimodal PDF Q&A (Text + Images)")

    text_model, img_model, img_proc, tokenizer, llm = load_models()

    question = st.text_input("Ask something from the PDF:")

    if st.button("Search"):

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # ---------------- TEXT SEARCH ----------------
        text_faiss = faiss.read_index(TEXT_FAISS_PATH)
        q_vec_text = text_model.encode(question, normalize_embeddings=True).astype("float32")

        D, I = text_faiss.search(np.array([q_vec_text]), TOP_K)
        I = I[0]

        st.subheader("📄 Relevant Text")
        context = ""

        for idx in I:
            cur.execute("SELECT page,chunk FROM text_chunks WHERE vector_index=?", (idx,))
            row = cur.fetchone()
            if row:
                page, chunk = row
                st.write(f"**Page {page}:** {chunk[:300]}...")
                context += chunk + "\n"

        # ---------------- IMAGE SEARCH ----------------
        img_faiss = faiss.read_index(IMG_FAISS_PATH)

        inp = img_proc(text=[question], return_tensors="pt")
        with torch.no_grad():
            img_q = img_model.get_text_features(**inp).cpu().numpy()
        img_q = img_q / np.linalg.norm(img_q)

        D2, I2 = img_faiss.search(img_q.astype("float32"), TOP_K)
        I2 = I2[0]

        st.subheader("🖼 Relevant Images")

        for idx in I2:
            cur.execute("SELECT page,image_path FROM images WHERE vector_index=?", (idx,))
            row = cur.fetchone()
            if row:
                page, img_path = row
                st.image(img_path, caption=f"Page {page}")

        # ---------------- LLM ANSWER ----------------
        st.subheader("🤖 Final Answer")
        answer = answer_llm(context, question, tokenizer, llm)
        st.write(answer)


if __name__ == "__main__":
    main()
