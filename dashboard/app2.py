import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="E-commerce Intelligence",
    page_icon="📈",
    layout="wide",
)


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect("warehouse/ecommerce.duckdb", read_only=True)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    con = get_con()
    fact_orders = con.execute("SELECT * FROM fact_orders").df()
    mart_sales = con.execute("SELECT * FROM mart_sales").df()
    monthly_history = con.execute(
        """
        SELECT month, category,
               SUM(ca_historique) AS ca,
               SUM(nb_commandes)  AS commandes
        FROM mart_monthly_history
        GROUP BY month, category
        ORDER BY month
        """
    ).df()
    return fact_orders, mart_sales, monthly_history


def fmt_usd(value: float) -> str:
    return f"${value:,.0f}"


def fmt_mad(value: float) -> str:
    return f"{value:,.0f} MAD"


def fmt_int(value: float) -> str:
    return f"{int(value):,}".replace(",", " ")


orders_df, mart_df, history_df = load_data()

if history_df["month"].dtype == "object":
    history_df["month"] = pd.to_datetime(history_df["month"], errors="coerce")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 1rem;}
    .dashboard-title {font-size: 2rem; font-weight: 700; margin-top: 2rem; margin-bottom: 0.2rem;}
    .dashboard-subtitle {color: #6b7280; margin-bottom: 1.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dashboard-title">E-commerce Intelligence Hub</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dashboard-subtitle">Vue consolidée des ventes, marges, marchés et tendances.</div>',
    unsafe_allow_html=True,
)

st.sidebar.header("Filtres globaux")
categories = sorted(orders_df["category"].dropna().unique().tolist())
countries = sorted(orders_df["user_country"].dropna().unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Catégories",
    options=categories,
    default=categories,
)
selected_countries = st.sidebar.multiselect(
    "Pays",
    options=countries,
    default=countries,
)

filtered_orders = orders_df[
    orders_df["category"].isin(selected_categories)
    & orders_df["user_country"].isin(selected_countries)
].copy()

filtered_mart = mart_df[mart_df["category"].isin(selected_categories)].copy()
filtered_history = history_df[history_df["category"].isin(selected_categories)].copy()

if filtered_orders.empty:
    st.warning("Aucune donnée disponible avec les filtres sélectionnés.")
    st.stop()

ca_total_usd = filtered_orders["amount_usd"].sum()
ca_total_mad = filtered_orders["amount_mad"].sum()
marge_totale = filtered_orders["margin_usd"].sum()
nb_commandes = filtered_orders["order_id"].nunique()
panier_moyen = ca_total_usd / nb_commandes if nb_commandes else 0

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("CA Total (USD)", fmt_usd(ca_total_usd))
kpi2.metric("CA Total (MAD)", fmt_mad(ca_total_mad))
kpi3.metric("Marge Totale", fmt_usd(marge_totale))
kpi4.metric("Commandes", fmt_int(nb_commandes))
kpi5.metric("Panier Moyen", fmt_usd(panier_moyen))

st.divider()

tab_overview, tab_products, tab_markets, tab_history = st.tabs(
    ["Vue Executive", "Produits", "Marchés", "Historique"]
)

with tab_overview:
    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("Performance par catégorie")
        perf_cat = (
            filtered_orders.groupby("category", as_index=False)
            .agg(
                ca_usd=("amount_usd", "sum"),
                marge_usd=("margin_usd", "sum"),
                commandes=("order_id", "nunique"),
            )
            .sort_values("ca_usd", ascending=False)
        )
        fig_perf = px.bar(
            perf_cat,
            x="category",
            y="ca_usd",
            color="marge_usd",
            title="CA par catégorie (couleur = marge)",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    with right:
        st.subheader("Objectifs par catégorie")
        if not filtered_mart.empty:
            goals = filtered_mart[["category", "taux_realisation", "statut_objectif"]].copy()
            goals = goals.sort_values("taux_realisation", ascending=False)
            fig_goal = px.bar(
                goals,
                x="taux_realisation",
                y="category",
                orientation="h",
                color="statut_objectif",
                title="Taux de réalisation (%)",
                color_discrete_map={
                    "✅ Atteint": "#16a34a",
                    "⚠️ En cours": "#f59e0b",
                    "❌ Retard": "#ef4444",
                },
            )
            st.plotly_chart(fig_goal, use_container_width=True)
        else:
            st.info("La vue `mart_sales` ne contient pas de catégories après filtrage.")

with tab_products:
    st.subheader("Top produits")
    prod = (
        filtered_orders.groupby(["product_name", "category"], as_index=False)
        .agg(
            ca_usd=("amount_usd", "sum"),
            units_sold=("quantity", "sum"),
            marge_usd=("margin_usd", "sum"),
        )
        .sort_values("ca_usd", ascending=False)
    )

    p1, p2 = st.columns(2)
    with p1:
        fig_top = px.bar(
            prod.head(15),
            x="ca_usd",
            y="product_name",
            orientation="h",
            color="category",
            title="Top 15 produits par CA",
        )
        st.plotly_chart(fig_top, use_container_width=True)
    with p2:
        fig_scatter = px.scatter(
            prod,
            x="ca_usd",
            y="marge_usd",
            size="units_sold",
            color="category",
            hover_name="product_name",
            title="Rentabilité produit (CA vs Marge)",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.dataframe(
        prod.rename(
            columns={
                "product_name": "Produit",
                "category": "Catégorie",
                "ca_usd": "CA (USD)",
                "units_sold": "Unités vendues",
                "marge_usd": "Marge (USD)",
            }
        ),
        use_container_width=True,
    )

with tab_markets:
    st.subheader("Analyse géographique")
    by_country = (
        filtered_orders.groupby("user_country", as_index=False)
        .agg(
            ca_usd=("amount_usd", "sum"),
            ca_mad=("amount_mad", "sum"),
            nb_commandes=("order_id", "nunique"),
        )
        .sort_values("ca_usd", ascending=False)
    )
    by_country["panier_moyen"] = by_country["ca_usd"] / by_country["nb_commandes"].clip(lower=1)

    m1, m2 = st.columns([1.4, 1])
    with m1:
        fig_map = px.choropleth(
            by_country,
            locations="user_country",
            color="ca_usd",
            hover_name="user_country",
            color_continuous_scale="Teal",
            title="CA par pays (USD)",
        )
        st.plotly_chart(fig_map, use_container_width=True)
    with m2:
        fig_rank = px.bar(
            by_country.head(10),
            x="ca_usd",
            y="user_country",
            orientation="h",
            title="Top 10 pays par CA",
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    st.dataframe(
        by_country.rename(
            columns={
                "user_country": "Pays",
                "ca_usd": "CA (USD)",
                "ca_mad": "CA (MAD)",
                "nb_commandes": "Commandes",
                "panier_moyen": "Panier moyen (USD)",
            }
        ),
        use_container_width=True,
    )

with tab_history:
    st.subheader("Tendances temporelles")
    if filtered_history.empty:
        st.info("Aucune donnée historique disponible pour les catégories sélectionnées.")
    else:
        h1, h2 = st.columns(2)
        with h1:
            fig_trend = px.line(
                filtered_history,
                x="month",
                y="ca",
                color="category",
                markers=True,
                title="Évolution du CA",
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        with h2:
            fig_cmd = px.bar(
                filtered_history,
                x="month",
                y="commandes",
                color="category",
                barmode="group",
                title="Commandes par mois",
            )
            st.plotly_chart(fig_cmd, use_container_width=True)

st.caption("Dashboard Streamlit - Version professionnelle avec filtres globaux et vues multi-angles.")
