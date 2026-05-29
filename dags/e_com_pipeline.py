import sys
sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from ingestion.fetch_products      import fetch_products
from ingestion.fetch_orders        import fetch_orders
from ingestion.fetch_rates         import fetch_rates
from ingestion.fetch_local_sources import (
    ingest_csv_margins, ingest_csv_shipping,
    ingest_excel_objectifs, ingest_sqlite_history
)
from transform.build_dim_products  import build_dim_products
from transform.build_fact_orders   import build_fact_orders
from transform.build_mart_sales    import build_mart_sales
from warehouse.loader_minio              import load_all

default_args = {
    "owner":            "data-team",
    "retries":          3,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
    "depends_on_past":  False,
}

def ingest_all_local():
    ingest_csv_margins()
    ingest_csv_shipping()
    ingest_excel_objectifs()
    ingest_sqlite_history()

with DAG(
    dag_id="ecommerce_pipeline",
    default_args=default_args,
    description="Pipeline e-commerce : ingestion → transform → warehouse",
    schedule="0 */6 * * *",       
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["ecommerce", "production"],
) as dag:

    ingest_products = PythonOperator(
        task_id="ingest_products_api",
        python_callable=fetch_products,
    )
    ingest_orders = PythonOperator(
        task_id="ingest_orders_api",
        python_callable=fetch_orders,
    )
    ingest_rates = PythonOperator(
        task_id="ingest_rates_api",
        python_callable=fetch_rates,
    )
    ingest_local = PythonOperator(
        task_id="ingest_local_sources",
        python_callable=ingest_all_local,
    )
    transform_products = PythonOperator(
        task_id="transform_dim_products",
        python_callable=build_dim_products,
    )
    transform_orders = PythonOperator(
        task_id="transform_fact_orders",
        python_callable=build_fact_orders,
    )
    transform_sales = PythonOperator(
        task_id="transform_mart_sales",
        python_callable=build_mart_sales,
    )
    load_warehouse = PythonOperator(
        task_id="load_to_duckdb",
        python_callable=load_all,
    )

    # Dépendances
    [ingest_products, ingest_local]                    >> transform_products
    [ingest_orders, ingest_rates, transform_products]  >> transform_orders
    [transform_orders, ingest_local]                   >> transform_sales
    transform_sales                                    >> load_warehouse