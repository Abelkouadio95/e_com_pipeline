# warehouse/minio_client.py
import boto3
import s3fs
import os

MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS    = os.getenv("MINIO_ACCESS_KEY", "minioadmin01")
MINIO_SECRET    = os.getenv("MINIO_SECRET_KEY", "minioadmin01")
BUCKET          = "ecommerce-lake"

# Layers du Data Lake
BRONZE = "bronze"
SILVER = "silver"
GOLD   = "gold"

def get_s3_client():
    """Client boto3 pour upload/download de fichiers"""
    return boto3.client("s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
    )

def get_s3fs():
    """Filesystem s3fs pour pandas/duckdb (lecture Parquet)"""
    return s3fs.S3FileSystem(
        endpoint_url=MINIO_ENDPOINT,
        key=MINIO_ACCESS,
        secret=MINIO_SECRET,
    )

def s3_path(layer: str, filename: str) -> str:
    """Construit un chemin S3 propre"""
    return f"s3://{BUCKET}/{layer}/{filename}"

#Upload un dict Python comme JSON dans MinIO
def upload_json(data: dict, layer: str, key: str):
    
    import json
    s3 = get_s3_client()
    s3.put_object(
        Bucket=BUCKET,
        Key=f"{layer}/{key}",
        Body=json.dumps(data, ensure_ascii=False, default=str),
        ContentType="application/json"
    )
    print(f"✅ Uploadé → s3://{BUCKET}/{layer}/{key}")

def upload_parquet(df, layer: str, key: str):
    """Upload un DataFrame pandas comme Parquet dans MinIO"""
    import io
    s3 = get_s3_client()
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.put_object(
        Bucket=BUCKET,
        Key=f"{layer}/{key}",
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )
    print(f"✅ Uploadé → s3://{BUCKET}/{layer}/{key}")

def read_json(layer: str, key: str) -> dict:
    """Lit un fichier JSON depuis MinIO"""
    import json
    s3 = get_s3_client()
    obj = s3.get_object(Bucket=BUCKET, Key=f"{layer}/{key}")
    return json.loads(obj["Body"].read())

def read_parquet(layer: str, key: str):
    """Lit un fichier Parquet depuis MinIO en DataFrame"""
    import pandas as pd
    fs = get_s3fs()
    path = f"{BUCKET}/{layer}/{key}"
    return pd.read_parquet(path, filesystem=fs)

def list_keys(layer: str, prefix: str = "") -> list:
    """Liste les fichiers d'un layer avec un préfixe optionnel"""
    s3 = get_s3_client()
    response = s3.list_objects_v2(
        Bucket=BUCKET,
        Prefix=f"{layer}/{prefix}"
    )
    if "Contents" not in response:
        return []
    return [obj["Key"] for obj in response["Contents"]]