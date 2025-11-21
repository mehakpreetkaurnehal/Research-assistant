# ingestion/prepare_raw_texts.py
"""
    Read metadata CSV, and for each paper, save the summary text to a .txt file
    in out_folder. Filename uses paper id safely, prepares next step (chunking) by heavy text files.
"""


# ingestion/prepare_raw_texts.py

import os
import pandas as pd

RAW_METADATA_CSV   = "data/raw/arxiv_metadata.csv"
SUMMARY_TEXT_FOLDER= "data/raw/summaries"

os.makedirs(SUMMARY_TEXT_FOLDER, exist_ok=True)

def prepare_summary_files():
    """
    Read the metadata CSV with summaries and write each summary to a .txt file.
    This helps for fallback or quick indexing of the abstract.
    """
    df = pd.read_csv(RAW_METADATA_CSV)
    for _, row in df.iterrows():
        paper_id = row["id"]
        summary  = row["summary"]
        # Prepare filename
        fname = f"{paper_id}.txt"
        path  = os.path.join(SUMMARY_TEXT_FOLDER, fname)
        # Write summary text
        with open(path, "w", encoding="utf-8") as f:
            f.write(summary)
    print(f"✔ Written summaries for {len(df)} papers in {SUMMARY_TEXT_FOLDER}")

if __name__ == "__main__":
    prepare_summary_files()





# import os
# import pandas as pd

# def save_summaries_to_txt(metadata_csv: str, out_folder: str):
#     """
#     Read metadata CSV, and for each paper, save the summary text to a .txt file
#     in out_folder. Filename uses paper id safely.
#     """
#     df = pd.read_csv(metadata_csv)
#     if not os.path.exists(out_folder):
#         os.makedirs(out_folder)
#     for _, row in df.iterrows():
#         # sanitize filename
#         paper_id = row["id"].split("/")[-1]
#         filename = f"{paper_id}.txt"
#         filepath = os.path.join(out_folder, filename)
#         with open(filepath, "w", encoding="utf-8") as f:
#             f.write(row["title"] + "\n\n")
#             f.write("Authors: " + ", ".join(eval(row["authors"])) + "\n\n")
#             f.write("Published: " + str(row["published"]) + "\n\n")
#             f.write(row["summary"])
#     print(f"Saved {len(df)} text files to {out_folder}")

# def main():
#     save_summaries_to_txt("data/raw/arxiv_metadata.csv", "data/raw/texts")

# if __name__ == "__main__":
#     main()
