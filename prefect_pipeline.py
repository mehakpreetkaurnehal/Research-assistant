from prefect import flow, task
import sys
sys.stdout.reconfigure(encoding='utf-8')

@task(retries=3, retry_delay_seconds=10)
def task_fetch():
    from ingestion.fetch_papers import fetch_arxiv_papers
    df = fetch_arxiv_papers("machine learning", max_results=50)
    df.to_csv("data/raw/arxiv_metadata.csv", index=False)


@task(retries=3, retry_delay_seconds=10)
def task_download_parse():
    from ingestion.download_and_parse import main as download_main
    download_main()


@task(retries=3, retry_delay_seconds=10)
def task_chunk_embed():
    from storage.chunk_and_embed_full import main as embed_main
    embed_main()


@flow(name="rag_pipeline")
def rag_pipeline():
    task_fetch()
    task_download_parse()
    task_chunk_embed()


if __name__ == "__main__":
    rag_pipeline()
