# run_machine_learning_ingestion.py

import time
import logging
import schedule

from ingestion.fetch_papers import main as fetch_main    # metadata fetch for machine_learning
from ingestion.download_and_parse import main as download_main  # download & parse full texts
from storage.chunk_and_embed_full import main as embed_main    # chunk & embed

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s %(levelname)s %(message)s",
    filename = "logs/ml_ingestion_schedule.log",
    filemode = "a"
)

CATEGORY = "machine_learning"
MAX_RESULTS = 50

def ingestion_job_ml():
    logging.info("=== Starting ML ingestion job ===")
    try:
        logging.info(f"Fetching metadata for category: {CATEGORY}")
        fetch_main(category=CATEGORY, query=None, max_results=MAX_RESULTS)

        logging.info(f"Downloading & parsing PDFs for category: {CATEGORY}")
        download_main(category=CATEGORY)

        logging.info(f"Chunking & embedding full text for category: {CATEGORY}")
        embed_main(category=CATEGORY)

    except Exception as e:
        logging.error(f"[ERROR] ML ingestion pipeline failed: {e}")

    logging.info("=== ML ingestion job complete ===")

def main():
    # Example schedule: every day at 03:00 AM
    schedule.every().day.at("03:00").do(ingestion_job_ml)

    logging.info("Scheduler for ML ingestion started.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # check every minute

if __name__ == "__main__":
    main()
