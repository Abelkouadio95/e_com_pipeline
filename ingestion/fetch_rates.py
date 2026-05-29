import requests, json, os
from datetime import datetime, timezone
from warehouse.minio_client import upload_json, BRONZE

APP_ID = "c0dcf9d4184142ca88f1a6d149b786d3" # inscription gratuite sur openexchangerates.org pour obtenir une clé API (app_id) et accéder aux taux de change en temps réel.

def fetch_rates():
    
    response = requests.get(
        "https://openexchangerates.org/api/latest.json",
        params={"app_id": APP_ID},
        timeout=10
    )
    response.raise_for_status()
    
    data = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "data": response.json()
    }
    # Sauvegarde locale (optionnelle)
    #path = f"data/raw/rates/{datetime.today().date()}.json"
    #with open(path, "w") as f:
    #    json.dump(data, f, indent=2)

    #print(f"✅ Taux ingérés : {data['data']['rates']}")
    #return path

    # Upload dans MinIO
    key = f"rates/{datetime.today().date()}.json"
    upload_json(data, BRONZE, key)
    print(f"✅ Taux ingérés : {data['data']['rates']} → {BRONZE}/{key}")
    return key