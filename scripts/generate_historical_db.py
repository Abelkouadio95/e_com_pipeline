import sqlite3
import os
import random
from datetime import datetime, timedelta


COUNTRIES = ["US", "FR", "MA", "DE", "GB", "ES", "IT", "CA"]
CATEGORIES = ["electronics", "jewelery", "men's clothing", "women's clothing"]

PRODUCTS = {
    "electronics":      [(1, "Fjallraven Backpack", 109.95), (2, "Mens Casual Slim Fit", 22.3)],
    "jewelery":         [(5, "John Hardy Bracelet", 695.0),  (6, "Solid Gold Petite", 168.0)],
    "men's clothing":   [(3, "Mens Cotton Jacket", 55.99),   (4, "Mens Casual Trouser", 15.99)],
    "women's clothing": [(7, "Opna Moisture Shirt", 7.95),   (8, "MBJ Womens Solid", 9.85)],
}

con = sqlite3.connect("data/historical/orders_history.db")
cursor = con.cursor()
cursor.execute("DROP TABLE IF EXISTS orders_history")
cursor.execute("""
    CREATE TABLE orders_history (
        id            INTEGER PRIMARY KEY,
        date          TEXT,
        product_id    INTEGER,
        product_name  TEXT,
        category      TEXT,
        quantity      INTEGER,
        unit_price    REAL,
        amount_usd    REAL,
        country       TEXT,
        user_id       INTEGER
    )
""")

rows = []
for i in range(1, 10001):                           # 10000 commandes sur 12 mois
    date = datetime(2024, 1, 1) + timedelta(
        days=random.randint(0, 364),
        hours=random.randint(0, 23)
    )
    category = random.choice(CATEGORIES)
    product = random.choice(PRODUCTS[category])
    qty = random.randint(1, 4)

    # Saisonnalité : boost en décembre
    if date.month == 12:
        qty = qty * 2

    rows.append((
        i,
        date.strftime("%Y-%m-%d %H:%M:%S"),
        product[0], product[1], category,
        qty, product[2],
        round(product[2] * qty, 2),
        random.choice(COUNTRIES),
        random.randint(1, 20)
    ))

cursor.executemany("INSERT INTO orders_history VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
con.commit()
con.close()
print(f"✅ SQLite généré : 10000 commandes historiques")