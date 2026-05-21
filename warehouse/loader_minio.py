import duckdb
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ACCESS_KEY", "minioadmin01")
MINIO_SECRET   = os.getenv("MINIO_SECRET_KEY", "minioadmin01")
DB_PATH        = "warehouse/ecommerce.duckdb"

def get_connection():
    con = duckdb.connect(DB_PATH)
   
    con.execute(f"""
        SET s3_endpoint='{MINIO_ENDPOINT.replace("http://", "")}';
        SET s3_access_key_id='{MINIO_ACCESS}';
        SET s3_secret_access_key='{MINIO_SECRET}';
        SET s3_use_ssl=false;
        SET s3_url_style='path';
    """)
    return con

def load_all():
    con = get_connection()

    tables = {
        # Silver
        "dim_products":         "s3://ecommerce-lake/silver/dim_products.parquet",
        "fact_orders":          "s3://ecommerce-lake/silver/fact_orders.parquet",
        "ref_objectifs":        "s3://ecommerce-lake/silver/ref_objectifs.parquet",
        "ref_margins":          "s3://ecommerce-lake/silver/ref_margins.parquet",
        # Gold
        "mart_sales":           "s3://ecommerce-lake/gold/mart_sales.parquet",
        "mart_monthly_history": "s3://ecommerce-lake/gold/mart_monthly_history.parquet",
        # Bronze
        "orders_history":       "s3://ecommerce-lake/bronze/orders_history.parquet",
    }

    for table, path in tables.items():
        con.execute(f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT * FROM read_parquet('{path}')
        """)
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"✅ {table} chargé depuis MinIO : {count} lignes")

    con.close()