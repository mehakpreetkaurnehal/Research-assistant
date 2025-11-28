# ingestion/fetch_papers.py

import os
import pandas as pd
import time
import arxiv

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Configuration
OUTPUT_CSV        = "data/raw/arxiv_metadata.csv"
MAX_RESULTS       = 50      # number of papers to fetch (adjust as needed)
QUERY             = "machine learning"  # change to your topic
SLEEP_SECONDS     = 2.0      # delay between results to avoid API overload

def fetch_arxiv_papers(query: str, max_results: int = MAX_RESULTS, sleep_secs: float = SLEEP_SECONDS):
    """
    Fetch metadata of recent papers from arXiv matching the query.
    :param query: search query string
    :param max_results: how many results to fetch
    :param sleep_secs: delay between batches to avoid API overload
    :return: pandas DataFrame of papers metadata
    """
    client = arxiv.Client()
    search  = arxiv.Search(
        query      = query,
        max_results= max_results,
        sort_by    = arxiv.SortCriterion.SubmittedDate
    )

    records = []
    for result in client.results(search):
        # Extract the versioned ID (e.g., "2401.01234v1")
        entry_id   = result.entry_id.split("/")[-1]
        title      = result.title
        authors    = [a.name for a in result.authors]
        published  = result.published.strftime("%Y-%m-%d")
        summary    = result.summary
        pdf_url    = result.pdf_url

        rec = {
            "id"        : entry_id,
            "title"     : title,
            "authors"   : authors,
            "published" : published,
            "summary"   : summary,
            "pdf_url"   : pdf_url
        }
        records.append(rec)
        time.sleep(sleep_secs)

    df = pd.DataFrame(records)
    return df

def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df = fetch_arxiv_papers(QUERY, MAX_RESULTS, SLEEP_SECONDS)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Saved {len(df)} records to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()






















# import os
# import time
# import pandas as pd
# import arxiv  # arxiv.py library
# import fitz   # PyMuPDF
# from tqdm import tqdm

# RAW_METADATA_CSV  = "data/raw/arxiv_metadata.csv"
# DOWNLOAD_FOLDER    = "data/raw/pdfs"
# PARSED_TEXT_FOLDER = "data/raw/fulltexts"

# os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
# os.makedirs(PARSED_TEXT_FOLDER, exist_ok=True)

# def download_pdf(result, out_folder=DOWNLOAD_FOLDER):
#     paper_id = result.entry_id.split("/")[-1]
#     filename = f"{paper_id}.pdf"
#     path = os.path.join(out_folder, filename)
#     if not os.path.exists(path):
#         result.download_pdf(dirpath=out_folder, filename=filename)
#     return path

# def parse_pdf_to_text(pdf_path, out_folder=PARSED_TEXT_FOLDER):
#     doc = fitz.open(pdf_path)
#     full_text = []
#     for page in doc:
#         full_text.append(page.get_text())
#     doc.close()
#     base = os.path.basename(pdf_path).replace(".pdf", ".txt")
#     txt_path = os.path.join(out_folder, base)
#     with open(txt_path, "w", encoding="utf-8") as f:
#         f.write("\n".join(full_text))
#     return txt_path

# def main():
#     df = pd.read_csv(RAW_METADATA_CSV)
#     client = arxiv.Client()
#     for _, row in tqdm(df.iterrows(), total=len(df), desc="Downloading & Parsing PDFs"):
#         paper_id = row["id"]
#         print(f"Processing paper ID: {paper_id}")

#         # Build the search
#         search = arxiv.Search(id_list=[paper_id])
#         results_gen = client.results(search)
#         try:
#             result = next(results_gen)
#         except StopIteration:
#             print(f"⚠ Warning: No result found for arXiv ID {paper_id}. Skipping.")
#             continue

#         try:
#             pdf_path = download_pdf(result)
#             parse_pdf_to_text(pdf_path)
#         except Exception as e:
#             print(f"⚠ Error on paper {paper_id}: {e}")
#             continue

#         # Respect API timing
#         time.sleep(1)

#     print("✔ Done downloading and parsing full‐texts.")

# if __name__ == "__main__":
#     main()
