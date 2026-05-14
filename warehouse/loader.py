# warehouse/loader.py
import duckdb
import pandas as pd

DB_PATH = "warehouse/ecommerce.duckdb"

def load_all():
    con = duckdb.connect(DB_PATH)

    tables = {
        "dim_products":          "data/processed/dim_products.parquet",
        "fact_orders":           "data/processed/fact_orders.parquet",
        "mart_sales":            "data/processed/mart_sales.parquet",
        "mart_monthly_history":  "data/processed/mart_monthly_history.parquet",
        "ref_objectifs":         "data/processed/ref_objectifs.parquet",
        "ref_margins":           "data/processed/ref_margins.parquet",
        "orders_history":        "data/processed/orders_history.parquet",
    }

    for table_name, parquet_path in tables.items():
        con.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"✅ {table_name} chargé : {count} lignes")

    con.close()