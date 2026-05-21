import pandas as pd
import json, glob
from warehouse.minio_client import read_json, read_parquet, upload_parquet, list_keys, BRONZE, SILVER

def build_fact_orders():
    ## Charger les commandes brutes
    #files  = sorted(glob.glob("data/raw/orders/*.json"))
    #raw    = json.load(open(files[-1]))["data"]

    # Depuis MinIO BRONZE
    order_keys = list_keys(BRONZE, "orders/")
    latest_order   = sorted(order_keys)[-1].replace(f"bronze/", "")
    orders_raw      = read_json(BRONZE, latest_order)["data"]

    ## Charger les taux de change
    #rate_files = sorted(glob.glob("data/raw/rates/*.json"))
    #rates_raw  = json.load(open(rate_files[-1]))["data"]["rates"]

    # Depuis MinIO BRONZE
    rate_keys = list_keys(BRONZE, "rates/")
    latest_rate   = sorted(rate_keys)[-1].replace(f"bronze/", "")
    rates_raw      = read_json(BRONZE, latest_rate)["data"]["rates"]

    usd_to_mad = rates_raw.get("MAD", 10.0)
    usd_to_eur = rates_raw.get("EUR", 0.92)

    # Charger les références
    #products = pd.read_parquet("data/processed/dim_products.parquet")
    #shipping = pd.read_parquet("data/processed/ref_shipping.parquet")

    # Depuis MinIO SILVER
    products = read_parquet(SILVER, "dim_products.parquet")
    shipping = read_parquet(SILVER, "ref_shipping.parquet")

    rows = []
    for cart in orders_raw:
        for item in cart["products"]:
            product = products[products["product_id"] == item["productId"]]
            if product.empty:
                continue
            
            prod        = product.iloc[0]
            qty         = item["quantity"]
            amount_usd  = round(prod["price"] * qty, 2)
            zone        = prod.get("shipping_zone", "A")

            # Coût de livraison selon la zone
            ship_cost = shipping[
                (shipping["zone"] == zone) &
                (shipping["country_code"] == cart.get("user_country", "US"))
            ]
            shipping_cost_usd = ship_cost["cost_usd"].values[0] if not ship_cost.empty else 9.99

            rows.append({
                "order_id":           cart["id"],
                "user_id":            cart["userId"],
                "user_country":       cart.get("user_country", "US"),
                "order_date":         cart["date"],
                "product_id":         item["productId"],
                "product_name":       prod["title"],
                "category":           prod["category"],
                "quantity":           qty,
                "unit_price_usd":     prod["price"],
                "amount_usd":         amount_usd,
                "amount_mad":         round(amount_usd * usd_to_mad, 2),
                "amount_eur":         round(amount_usd * usd_to_eur, 2),
                "shipping_cost_usd":  shipping_cost_usd,
                "margin_usd":         round(amount_usd * prod["target_margin"], 2),
                "margin_mad":         round(amount_usd * prod["target_margin"] * usd_to_mad, 2),
            })

    df = pd.DataFrame(rows)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"]      = df["order_date"].dt.to_period("M").astype(str)
    df["weekday"]    = df["order_date"].dt.day_name()

    #df.to_parquet("data/processed/fact_orders.parquet", index=False)
    #print(f"✅ fact_orders : {len(df)} lignes")

    # Upload dans MinIO
    upload_parquet(df, SILVER, "fact_orders.parquet")
    print(f"✅ fact_orders → silver : {len(df)} lignes")
    return df