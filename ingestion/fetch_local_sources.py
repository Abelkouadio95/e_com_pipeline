from duckdb import df
import pandas as pd
import sqlite3
from datetime import datetime, timezone
from warehouse.minio_client import upload_parquet, BRONZE, SILVER

def ingest_csv_margins():
    df = pd.read_csv("data/static/categories_margins.csv")
    df["ingested_at"] = datetime.now(timezone.utc).isoformat()
    #localement
    #df.to_parquet("data/processed/ref_margins.parquet", index=False)
    #print(f"✅ Marges CSV chargées : {len(df)} catégories")

    # Upload dans MinIO
    upload_parquet(df, SILVER, "ref_margins.parquet")
    return df

def ingest_csv_shipping():
    df = pd.read_csv("data/static/shipping_costs.csv")
    df["ingested_at"] = datetime.now(timezone.utc).isoformat()
    #localement
    #df.to_parquet("data/processed/ref_shipping.parquet", index=False)
    #print(f"✅ Shipping CSV chargé : {len(df)} zones")

    # Upload dans MinIO
    upload_parquet(df, SILVER, "ref_shipping.parquet")
    return df

def ingest_excel_objectifs():
    xl = pd.ExcelFile("data/uploads/objectifs_Q1_2025.xlsx")
    
    objectifs = xl.parse("Objectifs_CA")
    budget    = xl.parse("Budget_Marketing")
    
    #objectifs.to_parquet("data/processed/ref_objectifs.parquet", index=False)
    #budget.to_parquet("data/processed/ref_budget.parquet", index=False)
    #print(f"✅ Excel chargé : objectifs + budget")

    # Upload dans MinIO
    upload_parquet(objectifs, SILVER, "ref_objectifs.parquet")
    upload_parquet(budget, SILVER, "ref_budget.parquet")
    return objectifs, budget


def ingest_sqlite_history():
    con = sqlite3.connect("data/historical/orders_history.db")
    df = pd.read_sql("SELECT * FROM orders_history", con)
    con.close()
    
    #df.to_parquet("data/processed/orders_history.parquet", index=False)
    #print(f"✅ Historique SQLite chargé : {len(df)} commandes")

    # Upload dans MinIO
    upload_parquet(df, BRONZE, "orders_history.parquet")
    return df