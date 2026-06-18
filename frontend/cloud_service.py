"""Self-contained analytics service for Streamlit Community Cloud.

The deployed Streamlit app reads compact Parquet assets committed with the
repository, so it does not require a separately hosted FastAPI container.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, silhouette_score
from sklearn.preprocessing import StandardScaler

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed" / "uci_online_retail_ii"


@lru_cache(maxsize=1)
def source_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.read_parquet(DATA_DIR / "customers.parquet")
    products = pd.read_parquet(DATA_DIR / "products.parquet")
    transactions = pd.read_parquet(DATA_DIR / "transactions.parquet")
    transactions["order_date"] = pd.to_datetime(transactions["order_date"])
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    return customers, products, transactions


@lru_cache(maxsize=1)
def customer_master() -> pd.DataFrame:
    customers, _, transactions = source_tables()
    completed = transactions[transactions["status"].eq("completed")].copy()
    completed["profit"] = completed["order_amount"] - completed["cost_amount"] - completed["discount_amount"]
    as_of = completed["order_date"].max() + pd.Timedelta(days=1)
    aggregates = completed.groupby("customer_id").agg(
        total_revenue=("order_amount", "sum"),
        total_profit=("profit", "sum"),
        order_count=("transaction_id", "nunique"),
        average_order_value=("order_amount", "mean"),
        last_purchase_date=("order_date", "max"),
        first_purchase_date=("order_date", "min"),
        product_diversity=("product_id", "nunique"),
    ).reset_index()
    aggregates["recency_days"] = (as_of - aggregates["last_purchase_date"]).dt.days.clip(lower=0)
    master = customers.merge(aggregates, on="customer_id", how="left")
    for column in (
        "total_revenue", "total_profit", "order_count", "average_order_value",
        "product_diversity",
    ):
        master[column] = master[column].fillna(0)
    master["recency_days"] = master["recency_days"].fillna(9999)
    master["campaign_response_rate"] = 0.0
    master["support_tickets"] = 0
    master["avg_resolution_hours"] = 0.0
    master["avg_satisfaction"] = 0.0
    master["tenure_days"] = (as_of - master["signup_date"]).dt.days.clip(lower=1)
    master["purchase_frequency"] = master["order_count"] / (master["tenure_days"] / 365.25).clip(lower=1)
    return add_clv(add_rfm(master))


def add_rfm(master: pd.DataFrame) -> pd.DataFrame:
    result = master.copy()
    active = result["order_count"] > 0
    result[["r_score", "f_score", "m_score"]] = 1
    if active.sum() >= 4:
        result.loc[active, "r_score"] = pd.qcut(result.loc[active, "recency_days"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
        result.loc[active, "f_score"] = pd.qcut(result.loc[active, "order_count"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
        result.loc[active, "m_score"] = pd.qcut(result.loc[active, "total_revenue"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    result["rfm_score"] = result[["r_score", "f_score", "m_score"]].sum(axis=1)
    result["segment"] = pd.cut(
        result["rfm_score"], [0, 4, 7, 9, 12],
        labels=["At-Risk", "Silver", "Gold", "Platinum"], include_lowest=True,
    ).astype(str)
    result.loc[~active, "segment"] = "At-Risk"
    return result


def add_clv(master: pd.DataFrame) -> pd.DataFrame:
    result = master.copy()
    retention = float(np.clip((result["order_count"] > 1).mean(), 0.05, 0.95))
    multiplier = sum((retention**year) / (1.10**year) for year in range(1, 4))
    result["predicted_clv"] = (result["average_order_value"] * result["purchase_frequency"] * 0.30 * multiplier).clip(lower=0)
    result["clv_rank"] = result["predicted_clv"].rank(ascending=False, method="dense").astype(int)
    return result


def dashboard() -> dict:
    customers, products, transactions = source_tables()
    master = customer_master()
    completed = transactions[transactions["status"].eq("completed")]
    monthly_frame = completed.set_index("order_date").resample("MS")["order_amount"].sum().reset_index()
    monthly = [{"month": row.order_date.strftime("%Y-%m"), "revenue": round(float(row.order_amount), 2)} for row in monthly_frame.itertuples()]
    category = completed.merge(products[["product_id", "category"]], on="product_id", how="left").groupby("category")["order_amount"].sum().sort_values(ascending=False).round(2).reset_index()
    segment = master.groupby("segment", observed=True).agg(customers=("customer_id", "count"), revenue=("total_revenue", "sum")).round(2).reset_index()
    geography = master.groupby("state").agg(customers=("customer_id", "count"), revenue=("total_revenue", "sum")).round(2).reset_index()
    churned = master["recency_days"] > 90
    recent_growth = 0.0
    if len(monthly_frame) > 1 and monthly_frame.order_amount.iloc[-2]:
        recent_growth = (monthly_frame.order_amount.iloc[-1] / monthly_frame.order_amount.iloc[-2] - 1) * 100
    health = np.clip(100 - master["recency_days"].clip(0, 365) / 365 * 60, 0, 100)
    return {
        "dataset": {
            "source": "UCI Online Retail II",
            "transactions": len(transactions),
            "products": len(products),
            "customers": len(customers),
            "date_start": transactions.order_date.min().isoformat(),
            "date_end": transactions.order_date.max().isoformat(),
            "markets": int(master.state.nunique()),
        },
        "kpis": {
            "customers": len(master),
            "active_customers": int((~churned).sum()),
            "revenue": round(float(master.total_revenue.sum()), 2),
            "profit": round(float(master.total_profit.sum()), 2),
            "churn_rate": round(float(churned.mean() * 100), 2),
            "retention_rate": round(float((~churned).mean() * 100), 2),
            "average_order_value": round(float(master.average_order_value.mean()), 2),
            "campaign_conversion_rate": 0.0,
            "revenue_growth_pct": round(float(recent_growth), 2),
            "customer_health_score": round(float(health.mean()), 2),
            "top_segment": str(master.segment.value_counts().index[0]),
        },
        "segments": segment.to_dict("records"),
        "geography": geography.to_dict("records"),
        "monthly_revenue": monthly,
        "category_revenue": category.to_dict("records"),
    }


def churn_predictions() -> list[dict]:
    master = customer_master()
    probability = np.clip(
        0.08 + master.recency_days.clip(0, 365) / 365 * 0.78
        - np.log1p(master.order_count) / np.log(25) * 0.16,
        0.01, 0.99,
    )
    result = master[["customer_id", "name"]].copy()
    result["churn_probability"] = probability.round(4)
    result["risk_level"] = pd.cut(probability, [0, .35, .65, 1], labels=["Low", "Medium", "High"], include_lowest=True).astype(str)
    return result.sort_values("churn_probability", ascending=False).to_dict("records")


def recommendations() -> list[dict]:
    master = customer_master()
    records = []
    for row in master.itertuples():
        if row.recency_days > 90 and row.total_revenue > 0:
            action, reason, priority = "Retention outreach", f"No purchase for {int(row.recency_days)} days", "High"
        elif row.segment == "Platinum":
            action, reason, priority = "VIP loyalty offer", "High RFM value and engagement", "Medium"
        elif row.order_count >= 2 and row.product_diversity <= 3:
            action, reason, priority = "Cross-sell adjacent category", "Repeat buyer with narrow category mix", "Medium"
        else:
            continue
        records.append({
            "customer_id": int(row.customer_id), "customer_name": row.name,
            "action": action, "reason": reason, "priority": priority,
            "expected_value": round(float(row.predicted_clv), 2),
        })
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(records, key=lambda item: (priority_order[item["priority"]], -item["expected_value"]))


def forecast(horizon: int) -> dict:
    _, _, transactions = source_tables()
    monthly = transactions[transactions.status.eq("completed")].set_index("order_date").resample("MS")["order_amount"].sum().asfreq("MS", fill_value=0)
    history = [{"month": index.strftime("%Y-%m"), "revenue": round(float(value), 2)} for index, value in monthly.items()]
    frame = pd.DataFrame({"target": monthly})
    for lag in (1, 2, 3, 6):
        frame[f"lag_{lag}"] = frame.target.shift(lag)
    frame["rolling_3"] = frame.target.shift(1).rolling(3).mean()
    frame["month"] = frame.index.month
    train = frame.dropna()
    features = [column for column in train if column != "target"]
    split = max(len(train) - max(2, len(train) // 4), 1)
    model = GradientBoostingRegressor(random_state=42, n_estimators=150, learning_rate=.05)
    model.fit(train.iloc[:split][features], train.iloc[:split].target)
    validation = train.iloc[split:]
    predictions = model.predict(validation[features])
    mae = float(mean_absolute_error(validation.target, predictions))
    rmse = float(mean_squared_error(validation.target, predictions) ** .5)
    mape = float(np.mean(np.abs((validation.target - predictions) / validation.target.replace(0, np.nan))) * 100)
    model.fit(train[features], train.target)
    extended = monthly.copy()
    output = []
    for _ in range(horizon):
        next_date = extended.index.max() + pd.offsets.MonthBegin()
        row = pd.DataFrame([{
            "lag_1": extended.iloc[-1], "lag_2": extended.iloc[-2], "lag_3": extended.iloc[-3],
            "lag_6": extended.iloc[-6], "rolling_3": extended.iloc[-3:].mean(), "month": next_date.month,
        }], columns=features)
        value = max(float(model.predict(row)[0]), 0)
        output.append({"month": next_date.strftime("%Y-%m"), "forecast": round(value, 2), "lower": round(max(0, value - 1.96 * rmse), 2), "upper": round(value + 1.96 * rmse, 2)})
        extended.loc[next_date] = value
    return {"history": history, "forecast": output, "metrics": {"model": "gradient_boosting", "mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 2)}}


def get(path: str):
    master = customer_master()
    if path == "/api/v1/dashboard":
        return dashboard()
    if path.startswith("/api/v1/customers/analytics/segments"):
        return master[["customer_id", "name", "rfm_score", "segment"]].to_dict("records")
    if path.startswith("/api/v1/customers/analytics/clv"):
        limit = 500
        return master[["customer_id", "name", "predicted_clv", "clv_rank"]].sort_values("clv_rank").head(limit).to_dict("records")
    if path.startswith("/api/v1/customers/analytics/clusters"):
        sample = master.sample(min(2000, len(master)), random_state=42)
        features = np.log1p(sample[["recency_days", "order_count", "total_revenue", "average_order_value"]].fillna(0))
        scaled = StandardScaler().fit_transform(features)
        labels = KMeans(n_clusters=4, n_init=10, random_state=42).fit_predict(scaled)
        rows = sample[["customer_id", "name"]].copy()
        rows["cluster"] = labels
        return {"clusters": rows.to_dict("records"), "silhouette_score": round(float(silhouette_score(scaled, labels)), 4)}
    if path.startswith("/api/v1/churn/predictions"):
        return churn_predictions()
    if path.startswith("/api/v1/customers/analytics/recommendations"):
        return recommendations()
    raise KeyError(path)


def post(path: str, payload: dict | None = None):
    payload = payload or {}
    if path == "/api/v1/forecast/revenue":
        return forecast(int(payload.get("horizon", 6)))
    if path == "/api/v1/churn/train":
        return {
            "best_model": "deployed risk heuristic",
            "metrics": {},
            "run_id": "streamlit-cloud-read-only",
        }
    raise KeyError(path)
