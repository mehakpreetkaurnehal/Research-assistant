# run_ml_ingestion_scheduler.py

import time
import logging
import schedule

from ingestion.fetch_papers import main as fetch_main
from ingestion.download_and_parse import main as download_main
from storage.chunk_and_embed_full import main as embed_main

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s %(levelname)s %(message)s",
    filename = "logs/ml_ingestion_schedule.log",
    filemode = "a"
)

CATEGORY    = "cs.AI"
MAX_RESULTS = 50

def ingestion_job_ml():
    logging.info("=== Starting ML ingestion job for category: %s ===", CATEGORY)
    try:
        fetch_main(category=CATEGORY, max_results=MAX_RESULTS)
        download_main(category=CATEGORY)
        embed_main(category=CATEGORY)
    except Exception as e:
        logging.error("ML ingestion pipeline failed: %s", e)
    logging.info("=== ML ingestion job complete ===")

def main():
    schedule.every().day.at("03:00").do(ingestion_job_ml)
    logging.info("Scheduler for ML ingestion started.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
