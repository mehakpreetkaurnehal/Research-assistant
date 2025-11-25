# run_ingestion_schedule.py

# in this added fetch_paperss as doing code different way
# run_ingestion_schedule.py

import os
import time
import schedule
import logging

from ingestion.fetch_paperss import main as fetch_main
from ingestion.download_and_parse import main as download_main
from storage.chunk_and_embed_full import main as embed_main
# optionally: from maintenance.cleanup_old_papers import main as cleanup_main

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    filename="logs/ingestion_schedule.log",
    filemode="a"
)

def ingestion_job():
    logging.info("== Starting ingestion job ==")
    categories = ["machine_learning", "biology", "physics"]  # adjust as needed
    for cat in categories:
        try:
            logging.info(f"Fetching metadata for category: {cat}")
            fetch_main(category=cat, query=None, max_results=50)

            logging.info(f"Downloading & parsing PDFs for category: {cat}")
            download_main(category=cat)         # ensure download_main accepts category

            logging.info(f"Chunking & embedding full text for category: {cat}")
            embed_main(category=cat)            # ensure embed_main accepts category

        except Exception as e:
            logging.error(f"Error in ingestion pipeline for category {cat}: {e}")

    # Optionally: cleanup old papers too
    # try:
    #     logging.info("Running cleanup of old papers")
    #     cleanup_main()
    # except Exception as e:
    #     logging.error(f"Error during cleanup: {e}")

    logging.info("== Ingestion job complete ==")

# Schedule the job (for example daily at 02:00). For testing you can change time.
schedule.every().day.at("02:00").do(ingestion_job)

if __name__ == "__main__":
    logging.info("Scheduler started.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user.")
