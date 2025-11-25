# dags/paper_ingestion_dag.py

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments for DAG
default_args = {
    'owner': 'you',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 21),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='paper_ingestion_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['ingestion'],
) as dag:

    def fetch_metadata_task(**kwargs):
        from ingestion.fetch_papers import main as fetch_main
        fetch_main(category='machine_learning')  # loop categories or parametrize

    def download_and_parse_task(**kwargs):
        from ingestion.download_and_parse import main as download_main
        download_main()

    def chunk_and_embed_task(**kwargs):
        from storage.chunk_and_embed_full import main as chunk_embed_main
        chunk_embed_main()

    def cleanup_old_papers_task(**kwargs):
        # import and run your cleanup logic here
        pass

    t1 = PythonOperator(
        task_id='fetch_metadata',
        python_callable=fetch_metadata_task,
        provide_context=True,
    )

    t2 = PythonOperator(
        task_id='download_and_parse',
        python_callable=download_and_parse_task,
        provide_context=True,
    )

    t3 = PythonOperator(
        task_id='chunk_and_embed',
        python_callable=chunk_and_embed_task,
        provide_context=True,
    )

    t4 = PythonOperator(
        task_id='cleanup_old_papers',
        python_callable=cleanup_old_papers_task,
        provide_context=True,
    )

    t1 >> t2 >> t3 >> t4
