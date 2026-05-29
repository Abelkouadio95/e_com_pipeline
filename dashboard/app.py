# dashboard/app.py
import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="E-commerce Intelligence", layout="wide")

@st.cache_resource
def get_con():
    return duckdb.connect("warehouse/ecommerce.duckdb", read_only=True)

con = get_con()

# ── Sidebar ────────────────────────────────────────────────
st.sidebar.title("🛒 E-commerce BI")
page = st.sidebar.radio("Navigation", [
    "📊 Vue Executive",
    "📦 Produits",
    "🌍 Marchés",
    "📈 Historique"
])

# ══════════════════════════════════════════════════════════
# PAGE 1 — Vue Executive
# ══════════════════════════════════════════════════════════
if page == "📊 Vue Executive":
    st.title("📊 Vue Executive")

    mart = con.execute("SELECT * FROM mart_sales").df()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CA Total (USD)",    f"${mart['ca_usd'].sum():,.0f}")
    col2.metric("CA Total (MAD)",    f"{mart['ca_mad'].sum():,.0f} MAD")
    col3.metric("Marge Totale",      f"${mart['marge_usd'].sum():,.0f}")
    col4.metric("Nb Commandes",      f"{mart['nb_commandes'].sum()}")

    st.divider()

    # Objectifs par catégorie
    st.subheader("🎯 Réalisation des objectifs")
    cols = st.columns(len(mart))
    for i, row in mart.iterrows():
        cols[i].metric(
            label=row["category"],
            value=f"{row['taux_realisation']}%",
            delta=row["statut_objectif"]
        )

    # CA par catégorie
    fig = px.bar(mart, x="category", y="ca_usd",
                 color="statut_objectif", title="CA par catégorie (USD)",
                 color_discrete_map={"✅ Atteint": "green",
                                     "⚠️ En cours": "orange",
                                     "❌ Retard": "red"})
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════
# PAGE 2 — Produits
# ══════════════════════════════════════════════════════════
elif page == "📦 Produits":
    st.title("📦 Analyse Produits")

    products = con.execute("""
        SELECT product_name, category, 
               SUM(amount_usd) as ca_usd,
               SUM(quantity)   as units_sold,
               SUM(margin_usd) as marge_usd
        FROM fact_orders
        GROUP BY product_name, category
        ORDER BY ca_usd DESC
    """).df()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top produits par CA")
        fig = px.bar(products.head(10), x="ca_usd", y="product_name",
                     orientation="h", color="category")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 Marge vs CA")
        fig = px.scatter(products, x="ca_usd", y="marge_usd",
                         size="units_sold", color="category",
                         hover_name="product_name")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Catalogue complet")
    st.dataframe(products, use_container_width=True)

# ══════════════════════════════════════════════════════════
# PAGE 3 — Marchés
# ══════════════════════════════════════════════════════════
elif page == "🌍 Marchés":
    st.title("🌍 Analyse par Marché")

    by_country = con.execute("""
        SELECT user_country,
               SUM(amount_usd)  as ca_usd,
               SUM(amount_mad)  as ca_mad,
               COUNT(DISTINCT order_id) as nb_commandes,
               AVG(amount_usd)  as panier_moyen
        FROM fact_orders
        GROUP BY user_country
        ORDER BY ca_usd DESC
    """).df()

    fig = px.choropleth(by_country, locations="user_country",
                        color="ca_usd", hover_name="user_country",
                        title="CA par pays (USD)")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(by_country, use_container_width=True)

# ══════════════════════════════════════════════════════════
# PAGE 4 — Historique
# ══════════════════════════════════════════════════════════
elif page == "📈 Historique":
    st.title("📈 Tendances historiques (12 mois)")

    history = con.execute("""
        SELECT month, category,
               SUM(ca_historique) as ca,
               SUM(nb_commandes)  as commandes
        FROM mart_monthly_history
        GROUP BY month, category
        ORDER BY month
    """).df()

    fig = px.line(history, x="month", y="ca",
                  color="category", title="Évolution du CA par catégorie")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(history, x="month", y="commandes",
                  color="category", title="Volume de commandes par mois",
                  barmode="stack")
    st.plotly_chart(fig2, use_container_width=True)