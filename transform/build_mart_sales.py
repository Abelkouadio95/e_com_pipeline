import pandas as pd
from warehouse.minio_client import read_parquet, upload_parquet, BRONZE, SILVER, GOLD


def build_mart_sales():

    #orders     = pd.read_parquet("data/processed/fact_orders.parquet")
    #history    = pd.read_parquet("data/processed/orders_history.parquet")
    #objectifs  = pd.read_parquet("data/processed/ref_objectifs.parquet")

    # Depuis MinIO
    orders    = read_parquet(SILVER, "fact_orders.parquet")
    objectifs = read_parquet(SILVER, "ref_objectifs.parquet")
    history = read_parquet(BRONZE, "orders_history.parquet")


    # KPIs par catégorie (données actuelles)
    by_category = orders.groupby("category").agg(
        ca_usd       = ("amount_usd", "sum"),
        ca_mad       = ("amount_mad", "sum"),
        marge_usd    = ("margin_usd", "sum"),
        nb_commandes = ("order_id",   "nunique"),
        nb_produits  = ("quantity",   "sum"),
    ).reset_index()

    # Comparaison avec objectifs janvier
    objectifs_jan = objectifs[["category", "ca_cible_janvier"]].copy()
    objectifs_jan.columns = ["category", "ca_cible_usd"]

    mart = by_category.merge(objectifs_jan, on="category", how="left")
    mart["taux_realisation"] = (mart["ca_usd"] / mart["ca_cible_usd"] * 100).round(1)
    mart["statut_objectif"]  = mart["taux_realisation"].apply(
        lambda x: "✅ Atteint" if x >= 100 else ("⚠️ En cours" if x >= 70 else "❌ Retard")
    )

    # KPIs globaux historiques par mois
    history["date"]  = pd.to_datetime(history["date"])
    history["month"] = history["date"].dt.to_period("M").astype(str)
    
    monthly = history.groupby(["month", "category"]).agg(
        ca_historique = ("amount_usd", "sum"),
        nb_commandes  = ("id",         "count"),
    ).reset_index()

    #mart.to_parquet("data/processed/mart_sales.parquet", index=False)
    #monthly.to_parquet("data/processed/mart_monthly_history.parquet", index=False)
    #print(f"✅ mart_sales : {len(mart)} catégories analysées")

    # Upload dans MinIO
    upload_parquet(mart, GOLD, "mart_sales.parquet")
    upload_parquet(monthly, GOLD, "mart_monthly_history.parquet")
    print(f"✅ mart_sales → gold : {len(mart)} catégories analysées")
    return mart