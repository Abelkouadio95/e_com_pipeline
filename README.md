# e_com_pipeline
# 🛒 E-commerce Data Pipeline

> Pipeline de données end-to-end simulant l'infrastructure data d'une entreprise e-commerce — de l'ingestion multi-sources jusqu'au dashboard analytique, avec une architecture Data Lake Bronze/Silver/Gold.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Airflow](https://img.shields.io/badge/Airflow-3.2.1-017CEE?logo=apacheairflow)
![MinIO](https://img.shields.io/badge/MinIO-Data%20Lake-C72E49?logo=minio)
![DuckDB](https://img.shields.io/badge/DuckDB-Warehouse-FFF000?logo=duckdb)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit)

---

## 📌 Aperçu du projet

Ce projet reproduit un pipeline data production-grade pour un contexte e-commerce. Il couvre l'ensemble de la chaîne :

```
Sources de données
(APIs + CSV + Excel + SQLite)
         │
         ▼
   Ingestion (Airflow)
         │
         ▼
  Bronze Layer (MinIO)        ← données brutes, horodatées, jamais modifiées
         │
         ▼
  Silver Layer (MinIO)        ← données nettoyées, typées, jointures effectuées
         │
         ▼
   Gold Layer (MinIO)         ← KPIs agrégés, prêts pour l'analyse
         │
         ▼
  Data Warehouse (DuckDB)     ← SQL analytique sur les fichiers Parquet S3
         │
         ▼
  Dashboard (Streamlit)       ← visualisation business interactive
```

---

## 🏗️ Architecture

### Stack technique

| Rôle | Outil | Justification |
|---|---|---|
| Orchestration | Apache Airflow 3.2.1 | DAGs, retry automatique, scheduling |
| Data Lake | MinIO | Object storage compatible S3, local |
| Format de stockage | Parquet | Colonnaire, compressé, rapide |
| Data Warehouse | DuckDB | SQL analytique embarqué, lit S3 nativement |
| Dashboard | Streamlit + Plotly | Visualisation rapide, Python-native |
| Conteneurisation | Docker Compose | Environnement reproductible |

### Architecture Bronze / Silver / Gold

```
ecommerce-lake/ (bucket MinIO)
│
├── bronze/                     ← Données brutes (jamais modifiées)
│   ├── products/
│   │   └── YYYY-MM-DD.json
│   ├── orders/
│   │   └── YYYY-MM-DD.json
│   ├── rates/
│   │   └── YYYY-MM-DD.json
│   └── orders_history/
│       └── full.parquet
│
├── silver/                     ← Données nettoyées et enrichies
│   ├── dim_products.parquet
│   ├── fact_orders.parquet
│   ├── ref_margins.parquet
│   ├── ref_objectifs.parquet
│   ├── ref_shipping.parquet
│   └── ref_budget.parquet
│
└── gold/                       ← KPIs agrégés pour la BI
    ├── mart_sales.parquet
    └── mart_monthly_history.parquet
```

---

## 📦 Sources de données

### APIs (temps réel)

| API | Données | Fréquence |
|---|---|---|
| [FakeStore API](https://fakestoreapi.com) | Produits, commandes, utilisateurs | Toutes les 6h |
| [Open Exchange Rates](https://openexchangerates.org) | Taux USD → MAD / EUR / GBP | Toutes les 6h |
| [RestCountries](https://restcountries.com) | Données géographiques par pays | Toutes les 6h |

### Sources statiques (fichiers locaux)

| Fichier | Format | Contenu |
|---|---|---|
| `categories_margins.csv` | CSV | Marge cible et zone de livraison par catégorie |
| `shipping_costs.csv` | CSV | Coûts de livraison par zone et pays |
| `objectifs_Q1_2025.xlsx` | Excel (2 onglets) | Objectifs CA et budget marketing Q1 |
| `orders_history.db` | SQLite | 6 000 commandes simulées sur 12 mois |

---

## 🔄 Le pipeline Airflow

Le DAG `ecommerce_pipeline` orchestre l'ensemble des tâches avec gestion des dépendances et retry automatique (3 tentatives, délai de 5 min).

```
ingest_products_api  ──┐
ingest_orders_api    ──┼──► transform_dim_products ──► transform_fact_orders ──► transform_mart_sales ──► load_to_duckdb
ingest_rates_api     ──┤
ingest_local_sources ──┘
```

**Scheduling : ** toutes les 6 heures (`0 */6 * * *`)

### Détail des tâches

```
INGESTION                    TRANSFORMATION              WAREHOUSE
─────────────────────        ────────────────────────    ──────────────────
ingest_products_api          transform_dim_products      load_to_duckdb
ingest_orders_api            transform_fact_orders
ingest_rates_api             transform_mart_sales
ingest_local_sources
```

---

## 🗄️ Modèle de données

### Couche Silver

**`dim_products`** — catalogue enrichi
```
product_id | title | category | price | target_margin |
estimated_cost | estimated_margin_usd | price_segment | shipping_zone
```

**`fact_orders`** — table de faits des commandes
```
order_id | user_id | user_country | order_date | product_id |
category | quantity | amount_usd | amount_mad | amount_eur |
shipping_cost_usd | margin_usd | margin_mad | month | weekday
```

### Couche Gold

**`mart_sales`** — KPIs par catégorie
```
category | ca_usd | ca_mad | marge_usd | nb_commandes |
ca_cible_usd | taux_realisation | statut_objectif
```

**`mart_monthly_history`** — évolution sur 12 mois
```
month | category | ca_historique | nb_commandes
```

---

## 📊 Dashboard

4 pages analytiques construites avec Streamlit et Plotly :

| Page | Contenu |
|---|---|
| 📊 Vue Executive | CA total MAD/USD, marge globale, taux de réalisation des objectifs Q1 |
| 📦 Produits | Top 10 produits par CA, scatter marge vs CA, catalogue complet |
| 🌍 Marchés | Carte choroplèthe par pays, panier moyen, volume par région |
| 📈 Historique | Évolution du CA sur 12 mois, volume de commandes par mois |

---

## 🚀 Installation et lancement

### Prérequis

- Docker Desktop avec WSL2 activé
- WSL2 (Ubuntu)
- Python 3.11+

### 1. Cloner le projet

```bash
git clone https://github.com/ton-username/ecommerce-pipeline.git
cd ecommerce-pipeline
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Édite le `.env` :

```bash
# Airflow
AIRFLOW_UID=1000
AIRFLOW_PROJ_DIR=.
FERNET_KEY=           # générer avec la commande ci-dessous

# API
OPEN_EXCHANGE_APP_ID= # inscription gratuite sur openexchangerates.org

# MinIO
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Dépendances pip
_PIP_ADDITIONAL_REQUIREMENTS=requests pandas duckdb openpyxl faker boto3 s3fs
```

Générer la Fernet Key :

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Générer les données statiques et historiques

```bash
# À exécuter une seule fois
python scripts/generate_static_files.py
python scripts/generate_historical_db.py
```

### 4. Lancer l'environnement Docker

```bash
docker compose up -d

# Vérifier que tous les services sont healthy
docker compose ps
```

| Service | URL | Credentials |
|---|---|---|
| Airflow UI | http://localhost:8080 | airflow / airflow |
| MinIO UI | http://localhost:9001 | minioadmin / minioadmin |

### 5. Lancer le pipeline

Depuis l'UI Airflow :
1. Active le DAG `ecommerce_pipeline`
2. Clique sur **Trigger DAG**
3. Surveille l'exécution dans la vue **Graph**

Ou depuis le terminal :

```bash
docker exec <scheduler_container> airflow dags trigger ecommerce_pipeline
```

### 6. Lancer le dashboard

```bash
# Dans un terminal WSL séparé
pip install streamlit plotly duckdb
streamlit run dashboard/app.py
```

Dashboard disponible sur http://localhost:8501

---

## 📁 Structure du projet

```
ecommerce-pipeline/
│
├── dags/
│   └── ecommerce_pipeline.py       ← DAG Airflow principal
│
├── ingestion/
│   ├── __init__.py
│   ├── fetch_products.py           ← API FakeStore → Bronze
│   ├── fetch_orders.py             ← API FakeStore → Bronze
│   ├── fetch_rates.py              ← API Exchange → Bronze
│   └── fetch_local_sources.py      ← CSV/Excel/SQLite → Bronze/Silver
│
├── transform/
│   ├── __init__.py
│   ├── build_dim_products.py       ← Bronze + Silver → Silver
│   ├── build_fact_orders.py        ← Bronze + Silver → Silver
│   └── build_mart_sales.py         ← Silver → Gold
│
├── warehouse/
│   ├── __init__.py
│   ├── loader.py                   ← Gold → DuckDB
│   └── minio_client.py             ← Client MinIO centralisé
│
├── dashboard/
│   └── app.py                      ← Streamlit 4 pages
│
├── scripts/
│   ├── generate_historical_db.py   ← Génère 6000 commandes SQLite
│   └── generate_static_files.py    ← Génère CSV et Excel de référence
│
├── data/
│   ├── static/                     ← CSV de référence
│   ├── uploads/                    ← Excel objectifs
│   └── historical/                 ← Base SQLite historique
│
├── docker-compose.yaml
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🧠 Concepts couverts

| Concept | Implémentation |
|---|---|
| Ingestion multi-sources | 3 APIs REST + CSV + Excel + SQLite |
| Data Lake | MinIO (compatible S3) |
| Architecture medallion | Bronze / Silver / Gold |
| Modélisation dimensionnelle | Dimensions + Faits + Marts |
| Orchestration | Apache Airflow, DAG avec dépendances |
| Retry & résilience | 3 retries, délai exponentiel |
| Format colonnaire | Parquet pour toutes les couches Silver/Gold |
| SQL analytique | DuckDB avec lecture S3 native |
| Visualisation | Streamlit + Plotly |
| Conteneurisation | Docker Compose (6 services) |

---

## 🔍 Exemples de requêtes DuckDB

```sql
-- Configuration MinIO
SET s3_endpoint='localhost:9000';
SET s3_access_key_id='minioadmin';
SET s3_secret_access_key='minioadmin';
SET s3_use_ssl=false;
SET s3_url_style='path';

-- CA par catégorie avec taux de réalisation
SELECT
    category,
    ROUND(ca_mad, 2)           AS chiffre_affaires_mad,
    ROUND(marge_usd, 2)        AS marge_usd,
    taux_realisation           AS taux_objectif_pct,
    statut_objectif
FROM read_parquet('s3://ecommerce-lake/gold/mart_sales.parquet')
ORDER BY ca_mad DESC;

-- Évolution mensuelle sur 12 mois
SELECT
    month,
    SUM(ca_historique)         AS ca_total,
    SUM(nb_commandes)          AS volume_commandes
FROM read_parquet('s3://ecommerce-lake/gold/mart_monthly_history.parquet')
GROUP BY month
ORDER BY month;

-- Top produits par marge
SELECT
    product_name,
    category,
    SUM(margin_mad)            AS marge_totale_mad,
    SUM(quantity)              AS unites_vendues
FROM read_parquet('s3://ecommerce-lake/silver/fact_orders.parquet')
GROUP BY product_name, category
ORDER BY marge_totale_mad DESC
LIMIT 10;
```

---

## 🛠️ Commandes utiles

```bash
# Voir les logs d'une tâche Airflow
docker exec <scheduler> airflow tasks logs ecommerce_pipeline ingest_products_api <date>

# Lister les fichiers dans MinIO
docker exec minio mc ls local/ecommerce-lake --recursive

# Inspecter le warehouse DuckDB
python -c "
import duckdb
con = duckdb.connect('warehouse/ecommerce.duckdb')
print(con.execute('SHOW TABLES').df())
"

# Redémarrer uniquement MinIO
docker compose restart minio

# Voir tous les runs du DAG
docker exec <scheduler> airflow dags list-runs -d ecommerce_pipeline
```

---

## 📈 Pistes d'amélioration

- [ ] Ajouter dbt pour la couche de transformation Silver → Gold
- [ ] Implémenter l'ingestion incrémentale (watermark par date)
- [ ] Ajouter des tests de qualité de données (Great Expectations)
- [ ] Remplacer FakeStore par une vraie source de données
- [ ] Dockeriser le dashboard Streamlit
- [ ] Ajouter des alertes email sur échec de tâche Airflow
- [ ] Migrer vers un vrai cluster S3 (AWS) pour scaler

---

## 📄 Licence

MIT — libre d'utilisation pour apprentissage et projets personnels.

---

> **Projet réalisé dans une démarche d'apprentissage du Data Engineering end-to-end.**
> *Ingestion → Data Lake → Transformation → Warehouse → Dashboard*