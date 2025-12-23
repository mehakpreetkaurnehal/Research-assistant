import os
import fitz  # PyMuPDF, for PDF reading + image extraction  :contentReference[oaicite:0]{index=0}
from PIL import Image
import pytesseract  # for OCR on images  :contentReference[oaicite:1]{index=1}
import sqlite3
import numpy as np
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer


import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

PDF_PATH = "D:\\Project\\research_assistant\\Images_extraction\\2511.20586v1.pdf"  

# if os.path.isfile(PDF_PATH):
#     print("path exists")
# else:
#     print("Path does not exist")

from PIL import Image
import pytesseract

img = Image.open(r"D:\Project\research_assistant\Images_extraction\data_imgdesc\images\page13_img0.png")

text = pytesseract.image_to_string(img, lang='eng')

print("---- OCR output ----")
print(text)

    
BASE_DIR = "data_imgdesc"             # base folder for this pipeline
IMG_DIR = os.path.join(BASE_DIR, "images")
STORE_DIR = os.path.join(BASE_DIR, "storage")

DB_PATH = os.path.join(STORE_DIR, "metadata.db")
FAISS_PATH = os.path.join(STORE_DIR, "docs_faiss.bin")

TEXT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# chunking parameters for splitting large text
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

def setup_dirs():
    """Create necessary folders if missing."""
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(STORE_DIR, exist_ok=True)

def extract_images(pdf_path):
    """Extract all embedded images from the PDF, save to disk, collect metadata."""
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        img_list = page.get_images(full=True)
        for img_index, img in enumerate(img_list):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            # convert if needed
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_path = os.path.join(IMG_DIR, f"page{page_num}_img{img_index}.png")
            pix.save(img_path)
            images.append({"page": page_num, "path": img_path})
    return images

def extract_text_pages(pdf_path):
    """Extract full text of each page, return list of page-texts, plus full combined text."""
    doc = fitz.open(pdf_path)
    page_texts = []
    for page in doc:
        page_texts.append(page.get_text())
    full_text = "\n".join(page_texts)
    return page_texts, full_text

def find_simple_captions(full_text):
    """Very naive caption extractor: find lines starting with 'Figure' or 'Fig.'"""
    captions = []
    for line in full_text.split("\n"):
        ln = line.strip()
        if ln.startswith(("Figure", "Fig.", "FIGURE", "FIG.")):
            captions.append(ln)
    return captions

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split long text into overlapping chunks."""
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + size, length)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == length:
            break
        start = end - overlap
    return chunks

def main():
    setup_dirs()

    # 1. Extract images from PDF
    images = extract_images(PDF_PATH)
    print("Extracted images:", len(images))

    # 2. Extract page texts + full text
    page_texts, full_text = extract_text_pages(PDF_PATH)

    # 3. Try to find captions from full_text
    captions = find_simple_captions(full_text)
    print("Found captions lines:", len(captions))

    # 4. Build list of “documents” to embed:
    #    a) text chunks from main text  
    #    b) caption-based descriptions  
    #    c) fallback OCR-based description for each extracted image
    docs = []

    # — a) text chunks
    for page_num, ptext in enumerate(page_texts):
        chunks = chunk_text(ptext)
        for chunk in chunks:
            docs.append({
                "pdf": os.path.basename(PDF_PATH),
                "page": page_num,
                "type": "text",
                "text": chunk,
                "image_path": None
            })

    # — b) captions (as image descriptions, without image path)
    for cap in captions:
        docs.append({
            "pdf": os.path.basename(PDF_PATH),
            "page": None,
            "type": "image_desc_caption",
            "text": cap,
            "image_path": None
        })

    # — c) For each extracted image: do OCR + add if yields non-empty text
    for img in images:
        try:
            im = Image.open(img["path"])
            ocr_text = pytesseract.image_to_string(im).strip()
            if ocr_text:
                docs.append({
                    "pdf": os.path.basename(PDF_PATH),
                    "page": img["page"],
                    "type": "image_desc_ocr",
                    "text": ocr_text,
                    "image_path": img["path"]
                })
        except Exception as e:
            print("⚠️ OCR failed for", img["path"], e)

    print("Total docs to embed:", len(docs))

    # 5. Embed all docs using text embedding model
    model = SentenceTransformer(TEXT_EMBED_MODEL)
    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True).astype("float32")

    # 6. Build FAISS index and store embeddings
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, FAISS_PATH)
    print("Saved FAISS index:", FAISS_PATH, "with dimension", dim)

    # 7. Store metadata in SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS docs (
            id INTEGER PRIMARY KEY,
            pdf_name TEXT,
            page_number INTEGER,
            content_type TEXT,
            text_content TEXT,
            image_path TEXT,
            vector_index INTEGER
        )
    """)
    for idx, d in enumerate(docs):
        cur.execute("""
            INSERT INTO docs (pdf_name, page_number, content_type, text_content, image_path, vector_index)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (d["pdf"], d["page"], d["type"], d["text"], d["image_path"], idx))
    conn.commit()
    conn.close()
    print("Metadata DB saved at:", DB_PATH)


if __name__ == "__main__":
    main()
