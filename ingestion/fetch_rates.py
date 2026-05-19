import requests, json, os
from datetime import datetime, timezone
from warehouse.minio_client import upload_json, BRONZE

APP_ID = "TON_APP_ID_ICI"

def fetch_rates():
    #os.makedirs("data/raw/rates", exist_ok=True)
    
    response = requests.get(
        "https://openexchangerates.org/api/latest.json",
        params={"app_id": 'c0dcf9d4184142ca88f1a6d149b786d3'},
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