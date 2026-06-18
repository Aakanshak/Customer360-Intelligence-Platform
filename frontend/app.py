"""Premium Streamlit experience for the Customer360 Intelligence Platform."""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from frontend.cloud_service import DATA_DIR
from frontend.cloud_service import get as local_get
from frontend.cloud_service import post as local_post

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
USE_LOCAL_DATA = os.getenv("USE_LOCAL_DATA", "").lower() in {"1", "true", "yes"} or not os.getenv("API_URL")
COLORS = {
    "violet": "#8B5CF6",
    "cyan": "#22D3EE",
    "blue": "#3B82F6",
    "green": "#34D399",
    "amber": "#FBBF24",
    "rose": "#FB7185",
    "muted": "#94A3B8",
}
SEGMENT_COLORS = {
    "Platinum": COLORS["violet"],
    "Gold": COLORS["amber"],
    "Silver": COLORS["cyan"],
    "At-Risk": COLORS["rose"],
}
RISK_COLORS = {"Low": COLORS["green"], "Medium": COLORS["amber"], "High": COLORS["rose"]}


st.set_page_config(
    page_title="Customer360 Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
        :root {--bg:#070B14;--panel:#0D1424;--panel2:#111B2E;--line:rgba(148,163,184,.14);--text:#F8FAFC;--muted:#94A3B8;}
        html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
        .stApp {background:
          radial-gradient(circle at 82% 0%, rgba(59,130,246,.12), transparent 28rem),
          radial-gradient(circle at 30% 20%, rgba(139,92,246,.08), transparent 30rem), var(--bg);}
        .block-container {padding:1.6rem 2.4rem 4rem;max-width:1500px;}
        h1,h2,h3 {font-family:'Manrope',sans-serif!important;color:var(--text)!important;letter-spacing:-.035em;}
        p, label, .stCaption {color:var(--muted);}
        [data-testid="stSidebar"] {background:linear-gradient(180deg,#0B1120 0%,#080D18 100%);border-right:1px solid var(--line);}
        [data-testid="stSidebar"] .block-container {padding:1.4rem 1rem;}
        [data-testid="stSidebar"] [role="radiogroup"] label {
          padding:.72rem .8rem;border-radius:10px;margin:.12rem 0;transition:.2s;border:1px solid transparent;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {background:rgba(139,92,246,.08);border-color:rgba(139,92,246,.15);}
        [data-testid="stSidebar"] [aria-checked="true"] {background:linear-gradient(90deg,rgba(139,92,246,.19),rgba(34,211,238,.06));}
        [data-testid="stMetric"] {
          background:linear-gradient(145deg,rgba(17,27,46,.98),rgba(11,18,32,.98));
          border:1px solid var(--line);padding:1.15rem 1.2rem;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.18);
        }
        [data-testid="stMetricLabel"] {color:var(--muted);}
        [data-testid="stMetricValue"] {font-family:'Manrope',sans-serif;color:var(--text);font-size:1.72rem;}
        [data-testid="stMetricDelta"] {font-weight:600;}
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {
          background:rgba(13,20,36,.72);border:1px solid var(--line);border-radius:16px;overflow:hidden;
        }
        .stButton>button {
          border:0;border-radius:10px;padding:.65rem 1rem;font-weight:700;color:white;
          background:linear-gradient(100deg,#7C3AED,#2563EB);box-shadow:0 8px 25px rgba(124,58,237,.22);
        }
        .stButton>button:hover {filter:brightness(1.12);transform:translateY(-1px);}
        .stSelectbox>div>div,.stMultiSelect>div>div,.stFileUploader section {
          background:var(--panel)!important;border-color:var(--line)!important;border-radius:12px!important;
        }
        .brand {display:flex;align-items:center;gap:.75rem;margin:.2rem .2rem 1.45rem;}
        .brand-mark {width:38px;height:38px;border-radius:12px;display:grid;place-items:center;color:white;font-size:20px;
          background:linear-gradient(135deg,#8B5CF6,#2563EB 58%,#22D3EE);box-shadow:0 8px 28px rgba(139,92,246,.35);}
        .brand-name {font-family:'Manrope';font-size:1.05rem;font-weight:800;color:white;line-height:1.05;}
        .brand-sub {font-size:.69rem;color:#64748B;letter-spacing:.11em;text-transform:uppercase;margin-top:.2rem;}
        .hero {position:relative;overflow:hidden;border:1px solid var(--line);border-radius:22px;padding:1.65rem 1.8rem;
          background:linear-gradient(120deg,rgba(17,27,46,.98),rgba(10,17,31,.96));margin-bottom:1.25rem;}
        .hero:after {content:"";position:absolute;right:-3rem;top:-6rem;width:22rem;height:22rem;border-radius:50%;
          background:radial-gradient(circle,rgba(34,211,238,.15),rgba(139,92,246,.07) 45%,transparent 70%);}
        .eyebrow {color:#A78BFA;font-weight:700;font-size:.72rem;text-transform:uppercase;letter-spacing:.16em;margin-bottom:.5rem;}
        .hero h1 {font-size:2.1rem;margin:0 0 .45rem;position:relative;z-index:1;}
        .hero p {font-size:.94rem;max-width:720px;margin:0;position:relative;z-index:1;}
        .source-row {display:flex;flex-wrap:wrap;gap:.55rem;margin-top:1rem;position:relative;z-index:1;}
        .pill {display:inline-flex;align-items:center;gap:.4rem;padding:.38rem .62rem;border-radius:999px;
          background:rgba(148,163,184,.07);border:1px solid var(--line);font-size:.72rem;color:#CBD5E1;}
        .live-dot {width:7px;height:7px;border-radius:50%;background:#34D399;box-shadow:0 0 0 4px rgba(52,211,153,.12);}
        .section-title {display:flex;align-items:end;justify-content:space-between;margin:1.4rem 0 .7rem;}
        .section-title h3 {font-size:1.08rem;margin:0;}
        .section-title span {font-size:.76rem;color:#64748B;}
        .insight {padding:1rem 1.05rem;border-radius:14px;background:linear-gradient(145deg,rgba(139,92,246,.1),rgba(34,211,238,.04));
          border:1px solid rgba(139,92,246,.18);min-height:108px;}
        .insight-label {font-size:.7rem;text-transform:uppercase;letter-spacing:.11em;color:#A78BFA;font-weight:700;}
        .insight-value {font-family:'Manrope';font-size:1.05rem;color:#F8FAFC;font-weight:700;margin:.35rem 0;}
        .insight-copy {font-size:.78rem;color:#94A3B8;line-height:1.45;}
        .priority-high {color:#FDA4AF;font-weight:700}.priority-medium {color:#FDE68A;font-weight:700}.priority-low {color:#86EFAC;font-weight:700}
        hr {border-color:var(--line)!important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60, show_spinner=False)
def api_get(path: str):
    if USE_LOCAL_DATA:
        return local_get(path)
    response = requests.get(f"{API_URL}{path}", timeout=60)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict | None = None):
    if USE_LOCAL_DATA:
        return local_post(path, payload)
    response = requests.post(f"{API_URL}{path}", json=payload or {}, timeout=240)
    response.raise_for_status()
    api_get.clear()
    return response.json()


def service_ready() -> bool:
    if USE_LOCAL_DATA:
        return DATA_DIR.exists()
    try:
        requests.get(f"{API_URL}/health", timeout=3).raise_for_status()
        return True
    except requests.RequestException:
        return False


def chart_style(figure: go.Figure, height: int = 390) -> go.Figure:
    figure.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=18, r=18, t=62, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#94A3B8"),
        title_font=dict(family="Manrope", color="#F8FAFC", size=17),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.08, x=1, xanchor="right"),
        hoverlabel=dict(bgcolor="#111B2E", bordercolor="#334155", font_color="#F8FAFC"),
    )
    figure.update_xaxes(gridcolor="rgba(148,163,184,.08)", zeroline=False)
    figure.update_yaxes(gridcolor="rgba(148,163,184,.08)", zeroline=False)
    return figure


def hero(title: str, subtitle: str, eyebrow: str = "Customer intelligence") -> None:
    dataset = api_get("/api/v1/dashboard").get("dataset", {})
    source = dataset.get("source", "Customer360")
    period = "No date range"
    if dataset.get("date_start") and dataset.get("date_end"):
        period = f"{str(dataset['date_start'])[:10]} → {str(dataset['date_end'])[:10]}"
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
          <div class="source-row">
            <span class="pill"><span class="live-dot"></span> Analytics online</span>
            <span class="pill">◫ {source}</span>
            <span class="pill">◎ {dataset.get('transactions', 0):,} transactions</span>
            <span class="pill">◌ {dataset.get('customers', 0):,} customers</span>
            <span class="pill">◷ {period}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, context: str = "") -> None:
    st.markdown(f'<div class="section-title"><h3>{title}</h3><span>{context}</span></div>', unsafe_allow_html=True)


def insight_card(label: str, value: str, copy: str) -> None:
    st.markdown(
        f'<div class="insight"><div class="insight-label">{label}</div><div class="insight-value">{value}</div><div class="insight-copy">{copy}</div></div>',
        unsafe_allow_html=True,
    )


inject_theme()
st.sidebar.markdown(
    """
    <div class="brand">
      <div class="brand-mark">✦</div>
      <div><div class="brand-name">Customer360</div><div class="brand-sub">Intelligence OS</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Summary",
        "Segmentation",
        "Customer Lifetime Value",
        "Churn Analytics",
        "Revenue Forecast",
        "Geography",
        "Recommendations",
        "Data Management",
    ],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption("ENTERPRISE ANALYTICS")
st.sidebar.markdown("**API status**  ·  🟢 Healthy" if service_ready() else "**API status**  ·  🔴 Offline")
st.sidebar.caption("Mode: Bundled analytics" if USE_LOCAL_DATA else f"Endpoint: {API_URL}")

if not service_ready():
    st.error("The analytics API is unavailable. Start FastAPI on port 8000 and refresh this page.")
    st.stop()

if page == "Executive Summary":
    hero("The pulse of your customer business", "A unified executive view of commercial performance, customer health, and the signals that deserve attention now.")
    data = api_get("/api/v1/dashboard")
    kpis = data["kpis"]
    columns = st.columns(5)
    columns[0].metric("Total customers", f"{kpis['customers']:,}", f"{kpis['active_customers']:,} active")
    columns[1].metric("Net revenue", f"£{kpis['revenue']:,.0f}", f"{kpis.get('revenue_growth_pct', 0):+.1f}% recent")
    columns[2].metric("Gross profit", f"£{kpis['profit']:,.0f}", f"{(kpis['profit'] / kpis['revenue'] * 100 if kpis['revenue'] else 0):.1f}% margin")
    columns[3].metric("Retention rate", f"{kpis['retention_rate']:.1f}%", f"{kpis['churn_rate']:.1f}% at risk", delta_color="inverse")
    columns[4].metric("Customer health", f"{kpis.get('customer_health_score', 0):.0f}/100", kpis["top_segment"])

    section("Performance trajectory", "Revenue movement and portfolio composition")
    left, right = st.columns([1.65, 1])
    monthly = pd.DataFrame(data["monthly_revenue"])
    if not monthly.empty:
        area = px.area(monthly, x="month", y="revenue", markers=True, title="Monthly revenue", color_discrete_sequence=[COLORS["violet"]])
        area.update_traces(line=dict(width=3), fillcolor="rgba(139,92,246,.18)", hovertemplate="<b>%{x}</b><br>£%{y:,.0f}<extra></extra>")
        left.plotly_chart(chart_style(area, 405), width="stretch")
    segments = pd.DataFrame(data["segments"])
    if not segments.empty:
        donut = px.pie(segments, names="segment", values="revenue", hole=.68, title="Revenue mix by segment", color="segment", color_discrete_map=SEGMENT_COLORS)
        donut.update_traces(textposition="outside", textinfo="percent+label", hovertemplate="<b>%{label}</b><br>£%{value:,.0f}<br>%{percent}<extra></extra>")
        right.plotly_chart(chart_style(donut, 405), width="stretch")

    section("Executive signals", "Automatically interpreted from current data")
    signal_cols = st.columns(3)
    with signal_cols[0]:
        insight_card("Portfolio leader", kpis["top_segment"], "The largest customer group by population. Use it as the anchor for differentiated service design.")
    with signal_cols[1]:
        insight_card("Average order", f"£{kpis['average_order_value']:,.0f}", "A practical benchmark for offer thresholds, free-shipping gates, and bundle construction.")
    with signal_cols[2]:
        insight_card("Campaign conversion", f"{kpis['campaign_conversion_rate']:.1f}%", "Response behavior across recorded campaign touches. Zero indicates that marketing data has not yet been loaded.")

    category = pd.DataFrame(data["category_revenue"])
    if not category.empty:
        section("Category contribution", "Where customer spend concentrates")
        tree = px.treemap(category, path=["category"], values="order_amount", color="order_amount", color_continuous_scale=["#162033", "#3B82F6", "#8B5CF6"])
        tree.update_traces(textinfo="label+value+percent root", texttemplate="<b>%{label}</b><br>£%{value:,.0f}<br>%{percentRoot:.1%}")
        st.plotly_chart(chart_style(tree, 390), width="stretch")

elif page == "Segmentation":
    hero("Know who your customers are", "RFM scoring translates purchase behavior into clear commercial segments; clustering reveals patterns beyond business rules.", "Customer strategy")
    segments = pd.DataFrame(api_get("/api/v1/customers/analytics/segments"))
    if segments.empty:
        st.info("No customer data is available yet.")
    else:
        counts = segments["segment"].value_counts().rename_axis("segment").reset_index(name="customers")
        c1, c2 = st.columns([1, 1.7])
        donut = px.pie(counts, names="segment", values="customers", hole=.64, title="Customer portfolio", color="segment", color_discrete_map=SEGMENT_COLORS)
        donut.update_traces(textinfo="percent+label", hovertemplate="<b>%{label}</b><br>%{value:,} customers<extra></extra>")
        c1.plotly_chart(chart_style(donut, 430), width="stretch")
        distribution = segments.groupby(["segment", "rfm_score"], observed=True).size().reset_index(name="customers")
        bars = px.bar(distribution, x="rfm_score", y="customers", color="segment", barmode="stack", title="RFM score distribution", color_discrete_map=SEGMENT_COLORS)
        c2.plotly_chart(chart_style(bars, 430), width="stretch")
        section("Customer assignments", f"{len(segments):,} scored profiles")
        st.dataframe(segments.sort_values(["rfm_score", "customer_id"], ascending=[False, True]), width="stretch", hide_index=True)
        with st.expander("Explore K-Means diagnostic"):
            st.json(api_get("/api/v1/customers/analytics/clusters"))

elif page == "Customer Lifetime Value":
    hero("Invest where value compounds", "Forward-looking customer value helps prioritize service levels, retention investment, and relationship-building.", "Value management")
    data = pd.DataFrame(api_get("/api/v1/customers/analytics/clv?limit=500"))
    if data.empty:
        st.info("No customer data is available yet.")
    else:
        metrics = st.columns(3)
        metrics[0].metric("Customers ranked", f"{len(data):,}")
        metrics[1].metric("Top predicted CLV", f"£{data.predicted_clv.max():,.0f}")
        metrics[2].metric("Median predicted CLV", f"£{data.predicted_clv.median():,.0f}")
        top = data.head(30).sort_values("predicted_clv")
        chart = px.bar(top, x="predicted_clv", y="name", orientation="h", hover_data=["customer_id"], title="Highest-value customer relationships", color="predicted_clv", color_continuous_scale=["#2563EB", "#8B5CF6", "#22D3EE"])
        chart.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart_style(chart, 610), width="stretch")
        section("CLV ranking", "Three-year value horizon")
        st.dataframe(data, width="stretch", hide_index=True)

elif page == "Churn Analytics":
    hero("See risk before it becomes loss", "Customer-level risk scores combine recency, value, service, and engagement signals into an actionable retention queue.", "Predictive intelligence")
    top_left, top_right = st.columns([1, 3])
    with top_left:
        if st.button("Train & compare models", type="primary", width="stretch"):
            with st.spinner("Training Logistic Regression, Random Forest, and XGBoost..."):
                try:
                    result = api_post("/api/v1/churn/train")
                    st.success(f"Best model: {result['best_model'].replace('_', ' ').title()}")
                except requests.HTTPError as exc:
                    st.error(exc.response.json().get("detail", str(exc)))
    top_right.caption("Training creates a versioned model artifact and compares accuracy, precision, recall, F1, and ROC AUC.")
    data = pd.DataFrame(api_get("/api/v1/churn/predictions"))
    if not data.empty:
        risk = data.risk_level.value_counts().rename_axis("risk").reset_index(name="customers")
        high_risk = int((data.risk_level == "High").sum())
        metrics = st.columns(3)
        metrics[0].metric("High-risk customers", f"{high_risk:,}", f"{high_risk / len(data) * 100:.1f}% of base", delta_color="inverse")
        metrics[1].metric("Average risk", f"{data.churn_probability.mean() * 100:.1f}%")
        metrics[2].metric("Customers scored", f"{len(data):,}")
        left, right = st.columns([1, 1.6])
        bar = px.bar(risk, x="risk", y="customers", color="risk", title="Risk distribution", color_discrete_map=RISK_COLORS, category_orders={"risk": ["Low", "Medium", "High"]})
        left.plotly_chart(chart_style(bar, 390), width="stretch")
        histogram = px.histogram(data, x="churn_probability", nbins=25, title="Probability distribution", color_discrete_sequence=[COLORS["rose"]])
        histogram.update_xaxes(tickformat=".0%")
        right.plotly_chart(chart_style(histogram, 390), width="stretch")
        section("Retention priority queue", "Highest risk first")
        st.dataframe(data.sort_values("churn_probability", ascending=False), width="stretch", hide_index=True)

elif page == "Revenue Forecast":
    hero("Plan beyond the rear-view mirror", "A monthly revenue outlook with chronological validation and confidence bounds for more grounded commercial planning.", "Revenue planning")
    horizon = st.slider("Forecast horizon", 1, 24, 6, format="%d months")
    result = api_post("/api/v1/forecast/revenue", {"horizon": horizon})
    history = pd.DataFrame(result["history"])
    forecast = pd.DataFrame(result["forecast"])
    figure = go.Figure()
    if not history.empty:
        figure.add_trace(go.Scatter(x=history.month, y=history.revenue, name="Actual", mode="lines", line=dict(color=COLORS["cyan"], width=3)))
    if not forecast.empty:
        figure.add_trace(go.Scatter(x=forecast.month, y=forecast.upper, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        figure.add_trace(go.Scatter(x=forecast.month, y=forecast.lower, mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(139,92,246,.15)", name="95% interval", hoverinfo="skip"))
        figure.add_trace(go.Scatter(x=forecast.month, y=forecast.forecast, name="Forecast", mode="lines+markers", line=dict(color=COLORS["violet"], width=3, dash="dot")))
    figure.update_layout(title="Monthly revenue outlook")
    st.plotly_chart(chart_style(figure, 500), width="stretch")
    model = result["metrics"]
    metrics = st.columns(4)
    metrics[0].metric("Model", str(model.get("model", "—")).replace("_", " ").title())
    metrics[1].metric("MAE", f"£{model['mae']:,.0f}" if model.get("mae") is not None else "—")
    metrics[2].metric("RMSE", f"£{model['rmse']:,.0f}" if model.get("rmse") is not None else "—")
    metrics[3].metric("MAPE", f"{model['mape']:.1f}%" if model.get("mape") is not None else "—")

elif page == "Geography":
    hero("Understand every market", "Compare customer concentration and revenue contribution across countries, states, or operating regions.", "Market intelligence")
    geo = pd.DataFrame(api_get("/api/v1/dashboard")["geography"])
    if not geo.empty:
        metrics = st.columns(3)
        metrics[0].metric("Markets", f"{len(geo):,}")
        metrics[1].metric("Leading market", str(geo.loc[geo.revenue.idxmax(), "state"]))
        metrics[2].metric("Top-market revenue", f"£{geo.revenue.max():,.0f}")
        top_geo = geo.nlargest(20, "revenue").sort_values("revenue")
        chart = px.bar(top_geo, x="revenue", y="state", orientation="h", color="customers", title="Top markets by revenue", color_continuous_scale=["#1E3A8A", "#3B82F6", "#22D3EE"])
        st.plotly_chart(chart_style(chart, 620), width="stretch")
        section("Market detail", "Revenue and customer footprint")
        st.dataframe(geo.sort_values("revenue", ascending=False), width="stretch", hide_index=True)

elif page == "Recommendations":
    hero("Turn insight into the next best action", "A prioritized commercial worklist connects customer signals to retention, loyalty, cross-sell, and campaign actions.", "Decision engine")
    data = pd.DataFrame(api_get("/api/v1/customers/analytics/recommendations"))
    if data.empty:
        st.info("No recommendations are available for the current customer base.")
    else:
        priorities = st.multiselect("Priority filter", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
        filtered = data[data.priority.isin(priorities)]
        metrics = st.columns(4)
        metrics[0].metric("Recommended actions", f"{len(filtered):,}")
        metrics[1].metric("High priority", f"{(filtered.priority == 'High').sum():,}")
        metrics[2].metric("Value represented", f"£{filtered.expected_value.sum():,.0f}")
        metrics[3].metric("Action types", f"{filtered.action.nunique():,}")
        action_counts = filtered.groupby(["action", "priority"]).size().reset_index(name="customers")
        chart = px.bar(action_counts, x="customers", y="action", color="priority", orientation="h", title="Action portfolio", color_discrete_map={"High": COLORS["rose"], "Medium": COLORS["amber"], "Low": COLORS["green"]})
        st.plotly_chart(chart_style(chart, 400), width="stretch")
        section("Action queue", "Sorted by priority and expected value")
        st.dataframe(filtered, width="stretch", hide_index=True)

else:
    hero("Govern the data foundation", "Load standardized business datasets, inspect quality results, and manage the analytical source powering every dashboard.", "Data operations")
    data = api_get("/api/v1/dashboard")
    dataset = data.get("dataset", {})
    status_cols = st.columns(4)
    status_cols[0].metric("Source", dataset.get("source", "—"))
    status_cols[1].metric("Transactions", f"{dataset.get('transactions', 0):,}")
    status_cols[2].metric("Products", f"{dataset.get('products', 0):,}")
    status_cols[3].metric("Markets", f"{dataset.get('markets', 0):,}")

    section("Load a dataset", "CSV and Excel · validation before persistence")
    left, right = st.columns([1, 1.5])
    with left:
        st.markdown("#### Quick demo")
        st.caption("Create a deterministic synthetic dataset for development and testing.")
        if USE_LOCAL_DATA:
            st.info("The cloud deployment uses the bundled UCI dataset in read-only mode.")
        elif st.button("Create demo dataset", width="stretch"):
            st.json(api_post("/api/v1/admin/seed", {"customer_count": 250, "seed": 42}))
    with right:
        dataset_type = st.selectbox("Dataset type", ["customers", "products", "transactions", "marketing", "support"], disabled=USE_LOCAL_DATA)
        uploaded = st.file_uploader("Drop CSV or Excel here", type=["csv", "xls", "xlsx"], disabled=USE_LOCAL_DATA)
        if uploaded and not USE_LOCAL_DATA and st.button("Validate & ingest", type="primary"):
            response = requests.post(
                f"{API_URL}/api/v1/ingestion/files",
                data={"dataset_type": dataset_type},
                files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                timeout=240,
            )
            if response.ok:
                api_get.clear()
                st.success("Dataset validated and loaded.")
                st.json(response.json())
            else:
                st.error(response.json().get("detail", response.text))

    section("Public data provenance", "Portfolio-safe attribution")
    st.info(
        "The included large public dataset is UCI Online Retail II by Daqing Chen: "
        "1,067,371 original transaction rows covering December 2009–December 2011, licensed CC BY 4.0."
    )
