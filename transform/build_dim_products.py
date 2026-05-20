import pandas as pd
#import json, glob
from warehouse.minio_client import read_json, read_parquet, upload_parquet, list_keys, BRONZE, SILVER


def build_dim_products():
    # Prendre le fichier le plus récent en local
    #files = sorted(glob.glob("data/raw/products/*.json"))
    #raw   = json.load(open(files[-1]))["data"]
    
    # Prendre le fichier le plus récent dans MinIO BRONZE
    all_keys = list_keys(BRONZE, "products/")
    latest   = sorted(all_keys)[-1].replace(f"bronze/", "")

    raw      = read_json(BRONZE, latest)["data"]
    df = pd.DataFrame(raw)

    margins  = read_parquet(SILVER, "ref_margins.parquet")
    #margins = pd.read_parquet("data/processed/ref_margins.parquet")

    # Nettoyage
    df = df.rename(columns={"id": "product_id"})
    df["title"] = df["title"].str.strip()
    df["price"] = df["price"].astype(float)
    
    # Jointure avec les marges
    df = df.merge(margins, left_on="category", right_on="category", how="left")
    
    # Enrichissement
    df["estimated_cost"]   = df["price"] * (1 - df["target_margin"])
    df["estimated_margin_usd"] = df["price"] * df["target_margin"]
    df["price_segment"] = pd.cut(df["price"],
        bins=[0, 25, 100, 300, float("inf")],
        labels=["budget", "mid", "premium", "luxe"]
    )

    #df.to_parquet("data/processed/dim_products.parquet", index=False)
    upload_parquet(df, SILVER, "dim_products.parquet")
    print(f"✅ dim_products → silver : {len(df)} produits")
    return df