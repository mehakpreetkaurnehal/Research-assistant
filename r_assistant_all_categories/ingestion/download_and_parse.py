# ingestion/download_and_parse.py

import os
import time
import pandas as pd
import arxiv
import fitz   # PyMuPDF
from tqdm import tqdm

RAW_METADATA_CSV   = "data/raw/arxiv_metadata.csv"
DOWNLOAD_FOLDER    = "data/raw/pdfs"
PARSED_TEXT_FOLDER = "data/raw/fulltexts"
SLEEP_SECONDS      = 1.0

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(PARSED_TEXT_FOLDER, exist_ok=True)

def download_pdf(result, out_folder=DOWNLOAD_FOLDER):
    paper_id = result.entry_id.split("/")[-1]
    filename = f"{paper_id}.pdf"
    path     = os.path.join(out_folder, filename)

    if os.path.exists(path):
        print(f"[Skipped] PDF already exists for {paper_id}")
    else:
        print(f"[Download] PDF for {paper_id} → {path}")
        result.download_pdf(dirpath=out_folder, filename=filename)
        print(f"[Downloaded] {path}")
    return path

def parse_pdf_to_text(pdf_path, out_folder=PARSED_TEXT_FOLDER):
    paper_id    = os.path.basename(pdf_path).replace(".pdf", "")
    txt_filename = f"{paper_id}.txt"
    txt_path     = os.path.join(out_folder, txt_filename)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[ERROR] Unable to open PDF {pdf_path}: {e}")
        return None

    text_pages = []
    for page_number, page in enumerate(doc, start=1):
        try:
            page_text = page.get_text()
        except Exception as e:
            print(f"   [WARN] Unable to extract page {page_number} of {paper_id}: {e}")
            page_text = ""
        text_pages.append(page_text)
    doc.close()

    full_text = "\n".join(text_pages)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"[Parsed] Full-text for {paper_id} → {txt_path}")
    return txt_path

def main(category: str = "cs.AI"):
    print("=== Starting PDF download & parse step for category:", category, "===")
    df     = pd.read_csv(RAW_METADATA_CSV)
    client = arxiv.Client()
    total  = len(df)
    print(f"Found {total} papers in metadata CSV.")

    for idx, row in tqdm(df.iterrows(), total=total, desc="Download & parse"):
        paper_id = str(row["id"])
        print(f"\nProcessing {idx+1}/{total} → paper_id: {paper_id}")

        search     = arxiv.Search(id_list=[paper_id])
        results_gen = client.results(search)

        try:
            result = next(results_gen)
        except StopIteration:
            print(f"[WARN] No result found in arXiv for ID {paper_id}. Skipping.")
            continue

        try:
            pdf_path = download_pdf(result)
            if pdf_path is None:
                continue
        except Exception as e:
            print(f"[ERROR] Failed to download PDF for {paper_id}: {e}")
            continue

        try:
            text_path = parse_pdf_to_text(pdf_path)
            if text_path is None:
                continue
        except Exception as e:
            print(f"[ERROR] Failed to parse PDF {pdf_path}: {e}")
            continue

        time.sleep(SLEEP_SECONDS)

    print("=== Completed PDF download & parse step for category:", category, "===")

if __name__ == "__main__":
    main()
