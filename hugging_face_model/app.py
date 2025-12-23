# app.py
import os
import sqlite3
import streamlit as st
from ingest import ingest_pdf, build_faiss_index, load_faiss_index, conn, embed_text, EMBEDDING_MODEL_NAME
import faiss
import numpy as np

st.set_page_config(page_title="PDF-RAG Chatbot", page_icon="📄")

st.title("PDF + Image (captions) RAG Chatbot")

# Upload PDF & build index
uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
if uploaded is not None:
    pdf_path = os.path.join("data", uploaded.name)
    with open(pdf_path, "wb") as f:
        f.write(uploaded.read())
    st.write("Processing PDF …")
    ingest_pdf(pdf_path)
    index = build_faiss_index()
    st.success("PDF ingested and index built!")
else:
    index = load_faiss_index()
    if index is None:
        st.info("Please upload a PDF to start.")

# Chat / query interface
if index is not None:
    question = st.text_input("Ask a question about the document:")
    if question:
        qvec = embed_text(question)
        qvec = qvec.reshape(1, -1)
        D, I = index.search(qvec, k=5)
        st.write("Relevant chunks / captions:")
        conn = sqlite3.connect("data/metadata.db")
        cur = conn.cursor()
        context = ""
        for idx in I[0]:
            if idx < 0:
                continue
            cur.execute("SELECT pdf_name, page_num, item_type, content FROM items WHERE id = ?", (int(idx),))
            r = cur.fetchone()
            if r:
                pdf_name, page_num, typ, content = r
                st.write(f"- **{pdf_name}** — page {page_num} — {typ}")
                st.write(content[:500] + ("..." if len(content) > 500 else ""))
                context += content + "\n\n"
        conn.close()

        # Build prompt for LLM
        prompt = f"Use the context below to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        st.write("Prompt sent to LLM:\n", prompt)

        # TODO: integrate your LLM here — e.g. OpenAI / Gemini etc.
        # For demo, just echo context
        st.write("**(LLM output would appear here)**")
