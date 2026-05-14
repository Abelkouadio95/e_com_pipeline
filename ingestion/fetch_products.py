import requests
import json
from datetime import datetime, timezone

RAW_PATH = "data/raw/products"

def fetch_products():
    url = "https://fakestoreapi.com/products"
    response = requests.get(url)
    if response.status_code == 200:
        products = response.json()
       
    else:
        print(f"Echec. Status code: {response.status_code}")
        return []
    
    data = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "source": "fakestoreapi",
        "endpoint": "/products",
        "record_count": len(response.json()),
        "data": products
    }
    
    path = f"{RAW_PATH}/{datetime.today().date()}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Produits ingérés : {data['record_count']} articles → {path}")
    return path

if __name__ == "__main__":
    fetch_products()