import requests, json
from datetime import datetime, timezone
from warehouse.minio_client import upload_json, BRONZE

def fetch_orders():

    carts = requests.get("https://fakestoreapi.com/carts", timeout=10).json()
    
    users = requests.get("https://fakestoreapi.com/users", timeout=10).json()


    users_map = {u["id"]: u for u in users}
    
    enriched_orders = []
    for cart in carts:
        user = users_map.get(cart["userId"], {})
        enriched_orders.append({
            **cart,
            "user_email":   user.get("email"),
            "user_city":    user.get("address", {}).get("city"),
            "user_country": "US",          
        })

    date = datetime.today().date()

    data_orders = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "data": enriched_orders
    }
    data_users = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "data": users
    }

    # Sauvegarde locale (optionnelle)
    #with open(f"data/raw/orders/{date}.json", "w") as f:
    #    json.dump(data_orders, f, indent=2)

    #with open(f"data/raw/users/{date}.json", "w") as f:
    #    json.dump(data_users, f, indent=2)

    #print(f"Commandes ingérées : {len(carts)} commandes, {len(users)} utilisateurs")

    # Upload dans MinIO
    key_orders = f"orders/{date}.json"
    upload_json(data_orders, BRONZE, key_orders)

    key_users = f"users/{date}.json"
    upload_json(data_users, BRONZE, key_users)

    print(f"✅ Commandes ingérées : {len(carts)} commandes, {len(users)} utilisateurs → {BRONZE}/{key_orders} + {BRONZE}/{key_users}")
    return key_orders, key_users