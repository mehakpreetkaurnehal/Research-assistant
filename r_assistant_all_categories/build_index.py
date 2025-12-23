import os
import sys
import json
import sqlite3
import fitz
import numpy as np
import faiss
from tqdm import tqdm
from PIL import Image

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoProcessor, AutoModel

from dotenv import load_dotenv

# ============================================================
# LOAD HF TOKEN FROM MAIN FOLDER
# ============================================================
ROOT_DIR = os.path.abspath(os.path.join(os.getcwd(), ".."))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(ENV_PATH)

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")


# ============================================================
# CONFIG
# ============================================================
PDF_PATH = r"D:\Project\research_assistant\r_assistant_all_categories\2511.20592v1.pdf"

BASE_DIR = "data"
IMG_DIR = os.path.join(BASE_DIR, "images")
STORE = os.path.join(BASE_DIR, "storage")

DB_PATH = os.path.join(STORE, "metadata.db")
TEXT_FAISS_PATH = os.path.join(STORE, "text_faiss.bin")
IMAGE_FAISS_PATH = os.path.join(STORE, "image_faiss.bin")

TEXT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
IMAGE_MODEL_NAME = "laion/CLIP-ViT-B-32-laion2B-s34B-b79K"   # safe, uses safetensors

CHUNK_SIZE = 800
OVERLAP = 150


# ============================================================
# SETUP DIRECTORIES
# ============================================================
def setup_dirs():
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(STORE, exist_ok=True)


# ============================================================
# INIT DB
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS text_chunks (
            id INTEGER PRIMARY KEY,
            page INTEGER,
            chunk TEXT,
            vector_index INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            page INTEGER,
            image_path TEXT,
            vector_index INTEGER
        )
    """)

    conn.commit()
    return conn


# ============================================================
# CHUNK PDF TEXT
# ============================================================
def chunk_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    chunks = []
    pages = []

    for p in range(len(doc)):
        text = doc[p].get_text()
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunks.append(text[start:end])
            pages.append(p)
            if end == len(text):
                break
            start = end - OVERLAP

    return chunks, pages


# ============================================================
# EXTRACT IMAGES
# ============================================================
def extract_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []

    for p in range(len(doc)):
        for idx, img in enumerate(doc[p].get_images()):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            img_path = f"{IMG_DIR}/page{p}_img{idx}.png"
            pix.save(img_path)
            images.append({"page": p, "path": img_path})

    return images


# ============================================================
# MAIN PIPELINE
# ============================================================
def process_pdf():

    setup_dirs()
    conn = init_db()
    cur = conn.cursor()

    print("\nLoading TEXT model (MiniLM)...")
    text_model = SentenceTransformer(TEXT_MODEL_NAME, use_auth_token=HF_TOKEN)

    print("\nLoading IMAGE model (CLIP)...")
    image_model = AutoModel.from_pretrained(IMAGE_MODEL_NAME, token=HF_TOKEN)
    image_proc  = AutoProcessor.from_pretrained(IMAGE_MODEL_NAME, token=HF_TOKEN)
    image_model.to("cpu")

    print("\nExtracting + chunking text...")
    chunks, chunk_pages = chunk_pdf(PDF_PATH)

    print("\nExtracting images...")
    images = extract_images(PDF_PATH)

    text_vectors = []
    image_vectors = []

    # ---------------- TEXT EMBEDDING ----------------
    print("\nEmbedding text chunks...")
    for i, chunk in enumerate(tqdm(chunks)):
        vec = text_model.encode(chunk, convert_to_numpy=True).astype("float32")
        text_vectors.append(vec)

    text_vectors = np.vstack(text_vectors)
    print("Text embedding shape:", text_vectors.shape)

    # Save to FAISS
    text_index = faiss.IndexFlatL2(text_vectors.shape[1])
    text_index.add(text_vectors)
    faiss.write_index(text_index, TEXT_FAISS_PATH)

    # Save text metadata
    for i, chunk in enumerate(chunks):
        cur.execute(
            "INSERT INTO text_chunks (page,chunk,vector_index) VALUES (?,?,?)",
            (chunk_pages[i], chunk, i)
        )

    conn.commit()


    # ---------------- IMAGE EMBEDDING ----------------
    print("\nEmbedding images...")
    for img in tqdm(images):
        im = Image.open(img["path"]).convert("RGB")
        inp = image_proc(images=im, return_tensors="pt")
        with torch.no_grad():
            vec = image_model.get_image_features(**inp).cpu().numpy()

        v = vec / np.linalg.norm(vec)
        image_vectors.append(v)

    image_vectors = np.vstack(image_vectors)
    print("Image embedding shape:", image_vectors.shape)

    # Save to FAISS
    image_index = faiss.IndexFlatL2(image_vectors.shape[1])
    image_index.add(image_vectors)
    faiss.write_index(image_index, IMAGE_FAISS_PATH)

    # Save image metadata
    for i, img in enumerate(images):
        cur.execute(
            "INSERT INTO images (page,image_path,vector_index) VALUES (?,?,?)",
            (img["page"], img["path"], i)
        )

    conn.commit()
    conn.close()

    print("\n✓ Completed! PDF embedded + stored successfully.")


if __name__ == "__main__":
    process_pdf()
