# run_pipeline.py

import logging
from datetime import datetime

# IMPORT your modules (adjust paths if needed)
from ingestion.fetch_papers import fetch_arxiv_papers
from ingestion.download_and_parse import main as download_parse_main
from storage.chunk_and_embed_full import main as chunk_embed_main
# Optional: if you implement archive later
# from archive.cleanup import archive_old_papers
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def task_fetch():
    logging.info("START task: fetch_papers")
    # >>> FIX: pass your query list or categories as needed
    df = fetch_arxiv_papers(query="machine learning", max_results=100)
    csv_path = "data/raw/arxiv_metadata.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    logging.info(f"Fetched {len(df)} papers. Saved to {csv_path}")
    return csv_path

def task_download_parse():
    logging.info("START task: download_and_parse")
    download_parse_main()
    logging.info("Completed download and parse")

def task_chunk_embed():
    logging.info("START task: chunk_and_embed")
    chunk_embed_main()
    logging.info("Completed chunk and embed")

def task_cleanup():
    logging.info("START task: cleanup/archive_old_data")
    # >>> NEW: placeholder for archive logic if implemented later
    # archive_old_papers()
    logging.info("Completed cleanup")

def run_all():
    logging.info("Pipeline run started at %s", datetime.now().isoformat())
    try:
        task_fetch()
        task_download_parse()
        task_chunk_embed()
        task_cleanup()
        logging.info("Pipeline run finished successfully")
    except Exception as e:
        logging.error("Pipeline failed: %s", str(e))

if __name__ == "__main__":
    run_all()
input("Press Enter to finish...")
