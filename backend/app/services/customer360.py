"""Customer master and reusable analytical feature builders."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Customer, MarketingActivity, SupportTicket, Transaction


def table_frame(db: Session, model: type) -> pd.DataFrame:
    return pd.read_sql_query(select(model.__table__), db.connection())


def build_customer360(db: Session, as_of_date: datetime | None = None) -> pd.DataFrame:
    customers = table_frame(db, Customer)
    if customers.empty:
        return customers
    transactions = table_frame(db, Transaction)
    marketing = table_frame(db, MarketingActivity)
    support = table_frame(db, SupportTicket)
    if transactions.empty:
        as_of = pd.Timestamp(as_of_date or datetime.utcnow())
        tx = pd.DataFrame({"customer_id": customers.customer_id})
    else:
        transactions["order_date"] = pd.to_datetime(transactions["order_date"])
        as_of = pd.Timestamp(as_of_date or (transactions["order_date"].max() + pd.Timedelta(days=1))).tz_localize(None)
        completed = transactions[transactions["status"].str.lower().eq("completed")].copy()
        completed["profit"] = completed["order_amount"] - completed["cost_amount"] - completed["discount_amount"]
        tx = completed.groupby("customer_id").agg(
            total_revenue=("order_amount", "sum"),
            total_profit=("profit", "sum"),
            order_count=("transaction_id", "nunique"),
            average_order_value=("order_amount", "mean"),
            last_purchase_date=("order_date", "max"),
            first_purchase_date=("order_date", "min"),
            product_diversity=("product_id", "nunique"),
        ).reset_index()
        tx["recency_days"] = (as_of - tx["last_purchase_date"]).dt.days.clip(lower=0)

    if marketing.empty:
        mk = pd.DataFrame({"customer_id": customers.customer_id})
    else:
        mk = marketing.groupby("customer_id").agg(
            campaigns_received=("campaign_id", "count"),
            campaign_responses=("campaign_response", "sum"),
            marketing_cost=("campaign_cost", "sum"),
        ).reset_index()
        mk["campaign_response_rate"] = mk["campaign_responses"] / mk["campaigns_received"].replace(0, np.nan)

    if support.empty:
        sp = pd.DataFrame({"customer_id": customers.customer_id})
    else:
        sp = support.groupby("customer_id").agg(
            support_tickets=("ticket_id", "count"),
            avg_resolution_hours=("resolution_time", "mean"),
            avg_satisfaction=("satisfaction_score", "mean"),
        ).reset_index()

    master = customers.merge(tx, on="customer_id", how="left").merge(mk, on="customer_id", how="left").merge(sp, on="customer_id", how="left")
    numeric_defaults = {
        "total_revenue": 0, "total_profit": 0, "order_count": 0, "average_order_value": 0,
        "product_diversity": 0, "campaigns_received": 0, "campaign_responses": 0,
        "marketing_cost": 0, "campaign_response_rate": 0, "support_tickets": 0,
        "avg_resolution_hours": 0, "avg_satisfaction": 0, "recency_days": 9999,
    }
    for col, default in numeric_defaults.items():
        if col not in master:
            master[col] = default
        master[col] = master[col].fillna(default)
    master["signup_date"] = pd.to_datetime(master["signup_date"])
    master["tenure_days"] = (as_of - master["signup_date"]).dt.days.clip(lower=1)
    master["purchase_frequency"] = master["order_count"] / (master["tenure_days"] / 365.25).clip(lower=1)
    return master


def customer_profile(db: Session, customer_id: int) -> dict | None:
    master = build_customer360(db)
    match = master[master.customer_id == customer_id]
    if match.empty:
        return None
    result = match.iloc[0].replace({np.nan: None}).to_dict()
    for key, value in list(result.items()):
        if isinstance(value, (pd.Timestamp, datetime)):
            result[key] = value.isoformat()
        elif isinstance(value, np.generic):
            result[key] = value.item()
    return result
