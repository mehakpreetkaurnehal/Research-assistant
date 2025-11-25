# ingestion/fetch_paperss.py

import os
import pandas as pd
import time
import arxiv

RAW_METADATA_CSV = "data/raw/arxiv_metadata.csv"

def fetch_arxiv_papers(query: str, max_results: int = 50, sleep_secs: float = 2.0, category: str = None):
    """
    Fetch metadata of recent papers from arXiv matching the query and optional category.
    :param query: search query string
    :param max_results: how many results to fetch
    :param sleep_secs: delay between results to avoid API overload
    :param category: optional category label (e.g., "cs.AI", "eess.AS")
    :return: pandas DataFrame of papers metadata
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query       = query,
        max_results = max_results,
        sort_by     = arxiv.SortCriterion.SubmittedDate
    )

    records = []
    for result in client.results(search):
        entry_id   = result.entry_id.split("/")[-1]
        title      = result.title
        authors    = [a.name for a in result.authors]
        published  = result.published.strftime("%Y-%m-%d")
        summary    = result.summary
        pdf_url    = result.pdf_url

        rec = {
            "id":        entry_id,
            "title":     title,
            "authors":   authors,
            "published": published,
            "summary":   summary,
            "pdf_url":   pdf_url,
            "category":  category
        }
        records.append(rec)
        time.sleep(sleep_secs)

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(RAW_METADATA_CSV), exist_ok=True)
    df.to_csv(RAW_METADATA_CSV, index=False, encoding="utf-8")
    print(f"Saved {len(df)} records to {RAW_METADATA_CSV} for category {category}")
    return df

def main(category: str = "cs.AI", query: str = None, max_results: int = 50):
    if query is None:
        query = category.replace(".", " ").replace("_", " ")
    return fetch_arxiv_papers(query=query, max_results=max_results, category=category)

if __name__ == "__main__":
    main()
