"""Business analytics: RFM, CLV, KPIs, cohorts and recommendations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.db.models import Product, Transaction
from app.services.customer360 import build_customer360, table_frame


def rfm_segmentation(master: pd.DataFrame) -> pd.DataFrame:
    result = master.copy()
    active = result["order_count"] > 0
    result["r_score"] = 1
    result["f_score"] = 1
    result["m_score"] = 1
    if active.sum() >= 4:
        result.loc[active, "r_score"] = pd.qcut(result.loc[active, "recency_days"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
        result.loc[active, "f_score"] = pd.qcut(result.loc[active, "order_count"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
        result.loc[active, "m_score"] = pd.qcut(result.loc[active, "total_revenue"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    result["rfm_score"] = result[["r_score", "f_score", "m_score"]].sum(axis=1)
    result["segment"] = pd.cut(
        result["rfm_score"], bins=[0, 4, 7, 9, 12],
        labels=["At-Risk", "Silver", "Gold", "Platinum"], include_lowest=True,
    ).astype(str)
    result.loc[result["order_count"].eq(0), "segment"] = "At-Risk"
    return result


def cluster_customers(master: pd.DataFrame) -> dict:
    features = master[["recency_days", "order_count", "total_revenue", "average_order_value", "campaign_response_rate"]].replace([np.inf, -np.inf], 0).fillna(0)
    if len(features) < 4:
        return {"clusters": [], "silhouette_score": None}
    scaled = StandardScaler().fit_transform(np.log1p(features))
    k = min(4, max(2, len(features) // 10))
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(scaled)
    output = master[["customer_id", "name"]].copy()
    output["cluster"] = labels
    return {
        "clusters": output.to_dict("records"),
        "silhouette_score": round(float(silhouette_score(scaled, labels)), 4) if len(set(labels)) > 1 else None,
    }


def calculate_clv(master: pd.DataFrame, margin_rate: float = 0.30, horizon_years: int = 3) -> pd.DataFrame:
    result = master.copy()
    repeat_rate = (result["order_count"] > 1).mean()
    retention = float(np.clip(repeat_rate, 0.05, 0.95))
    discount_rate = 0.10
    multiplier = sum((retention ** year) / ((1 + discount_rate) ** year) for year in range(1, horizon_years + 1))
    result["predicted_clv"] = (result["average_order_value"] * result["purchase_frequency"] * margin_rate * multiplier).clip(lower=0)
    result["clv_rank"] = result["predicted_clv"].rank(ascending=False, method="dense").astype(int)
    return result


def executive_kpis(
    db: Session,
    master: pd.DataFrame | None = None,
    transactions: pd.DataFrame | None = None,
) -> dict:
    master = rfm_segmentation(build_customer360(db)) if master is None else rfm_segmentation(master)
    transactions = table_frame(db, Transaction) if transactions is None else transactions
    if master.empty:
        return {"customers": 0, "revenue": 0, "profit": 0, "churn_rate": 0, "retention_rate": 0}
    churned = master["recency_days"] > 90
    growth = 0.0
    if not transactions.empty:
        transactions["order_date"] = pd.to_datetime(transactions.order_date)
        monthly = transactions.set_index("order_date").resample("MS")["order_amount"].sum()
        if len(monthly) >= 2 and monthly.iloc[-2] != 0:
            growth = float((monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100)
    health = np.clip(
        100 - master["recency_days"].clip(0, 365) / 365 * 60
        + master["campaign_response_rate"] * 20
        + master["avg_satisfaction"].fillna(0) / 5 * 20,
        0, 100,
    )
    return {
        "customers": int(master.customer_id.nunique()),
        "active_customers": int((~churned).sum()),
        "revenue": round(float(master.total_revenue.sum()), 2),
        "profit": round(float(master.total_profit.sum()), 2),
        "churn_rate": round(float(churned.mean() * 100), 2),
        "retention_rate": round(float((1 - churned.mean()) * 100), 2),
        "average_order_value": round(float(master.average_order_value.mean()), 2),
        "campaign_conversion_rate": round(float(master.campaign_response_rate.mean() * 100), 2),
        "revenue_growth_pct": round(growth, 2),
        "customer_health_score": round(float(health.mean()), 2),
        "top_segment": str(master.segment.value_counts().index[0]),
    }


def dashboard_data(db: Session) -> dict:
    master_raw = build_customer360(db)
    master = rfm_segmentation(master_raw)
    transactions = table_frame(db, Transaction)
    products = table_frame(db, Product)
    if transactions.empty:
        monthly = []
        category = []
    else:
        transactions["order_date"] = pd.to_datetime(transactions.order_date)
        monthly_df = transactions.set_index("order_date").resample("MS")["order_amount"].sum().reset_index()
        monthly = [{"month": row.order_date.strftime("%Y-%m"), "revenue": round(float(row.order_amount), 2)} for row in monthly_df.itertuples()]
        merged = transactions.merge(products[["product_id", "category"]], on="product_id", how="left") if not products.empty else transactions.assign(category="Unknown")
        category = merged.groupby("category")["order_amount"].sum().sort_values(ascending=False).round(2).reset_index().to_dict("records")
    return {
        "dataset": {
            "source": "UCI Online Retail II" if len(transactions) > 100_000 else "Customer360 Demo / Uploaded Data",
            "transactions": int(len(transactions)),
            "products": int(len(products)),
            "customers": int(len(master)),
            "date_start": transactions["order_date"].min().isoformat() if not transactions.empty else None,
            "date_end": transactions["order_date"].max().isoformat() if not transactions.empty else None,
            "markets": int(master["state"].nunique()) if not master.empty else 0,
        },
        "kpis": executive_kpis(db, master_raw, transactions),
        "segments": master.groupby("segment", observed=True).agg(customers=("customer_id", "count"), revenue=("total_revenue", "sum")).round(2).reset_index().to_dict("records") if not master.empty else [],
        "geography": master.groupby("state").agg(customers=("customer_id", "count"), revenue=("total_revenue", "sum")).round(2).reset_index().to_dict("records") if not master.empty else [],
        "monthly_revenue": monthly,
        "category_revenue": category,
    }


def recommendations(master: pd.DataFrame) -> list[dict]:
    if master.empty:
        return []
    enriched = calculate_clv(rfm_segmentation(master))
    recs: list[dict] = []
    for row in enriched.itertuples():
        if row.recency_days > 90 and row.total_revenue > 0:
            action, reason, priority = "Retention outreach", f"No purchase for {int(row.recency_days)} days", "High"
        elif row.segment == "Platinum":
            action, reason, priority = "VIP loyalty offer", "High RFM value and engagement", "Medium"
        elif row.order_count >= 2 and row.product_diversity <= 1:
            action, reason, priority = "Cross-sell adjacent category", "Repeat buyer with narrow category mix", "Medium"
        elif row.campaign_response_rate >= 0.5:
            action, reason, priority = "Target next campaign", "Historically responsive to marketing", "Low"
        else:
            continue
        recs.append({
            "customer_id": int(row.customer_id), "customer_name": row.name, "action": action,
            "reason": reason, "priority": priority, "expected_value": round(float(row.predicted_clv), 2),
        })
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(recs, key=lambda item: (order[item["priority"]], -item["expected_value"]))


def exploratory_analytics(db: Session) -> dict:
    master = build_customer360(db)
    transactions = table_frame(db, Transaction)
    products = table_frame(db, Product)
    if master.empty:
        return {"demographics": [], "age_distribution": [], "cohorts": [], "product_performance": []}
    demographics = master.groupby("gender", dropna=False).agg(customers=("customer_id", "count"), revenue=("total_revenue", "sum")).round(2).reset_index().to_dict("records")
    age_bins = pd.cut(master.age, bins=[0, 24, 34, 44, 54, 64, 120], labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
    age_distribution = master.assign(age_band=age_bins).groupby("age_band", observed=True).size().rename("customers").reset_index().to_dict("records")
    cohorts: list[dict] = []
    product_performance: list[dict] = []
    if not transactions.empty:
        transactions["order_date"] = pd.to_datetime(transactions.order_date)
        signup = master.set_index("customer_id")["signup_date"]
        transactions["cohort"] = transactions.customer_id.map(signup).dt.to_period("M").astype(str)
        transactions["activity_month"] = transactions.order_date.dt.to_period("M").astype(str)
        cohorts = transactions.groupby(["cohort", "activity_month"]).customer_id.nunique().rename("active_customers").reset_index().to_dict("records")
        if not products.empty:
            merged = transactions.merge(products, on="product_id", how="left")
            product_performance = merged.groupby(["category", "product_name"]).agg(
                revenue=("order_amount", "sum"), units=("quantity", "sum"), orders=("transaction_id", "nunique")
            ).round(2).reset_index().to_dict("records")
    return {
        "demographics": demographics,
        "age_distribution": age_distribution,
        "cohorts": cohorts,
        "product_performance": product_performance,
    }
