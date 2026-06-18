"""Prepare and optionally load UCI Online Retail II into Customer360.

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
License: CC BY 4.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "external" / "uci_online_retail_ii" / "online_retail_II.xlsx"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "uci_online_retail_ii"


def read_source(path: Path) -> pd.DataFrame:
    workbook = pd.ExcelFile(path)
    frames = [pd.read_excel(path, sheet_name=sheet) for sheet in workbook.sheet_names]
    raw = pd.concat(frames, ignore_index=True)
    raw.columns = ["invoice", "stock_code", "description", "quantity", "invoice_date", "unit_price", "customer_id", "country"]
    return raw


def prepare(raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    frame = raw.copy()
    frame["invoice"] = frame["invoice"].astype("string").str.strip()
    frame["stock_code"] = frame["stock_code"].astype("string").str.strip()
    frame["description"] = frame["description"].astype("string").str.strip().str.title()
    frame["invoice_date"] = pd.to_datetime(frame["invoice_date"], errors="coerce")
    frame["customer_id"] = pd.to_numeric(frame["customer_id"], errors="coerce")
    frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce")
    frame["unit_price"] = pd.to_numeric(frame["unit_price"], errors="coerce")
    frame["country"] = frame["country"].astype("string").str.strip()
    frame["is_cancelled"] = frame["invoice"].str.upper().str.startswith("C") | frame["quantity"].lt(0)

    valid_customer = frame.dropna(subset=["customer_id", "invoice_date"]).copy()
    valid_customer["customer_id"] = valid_customer["customer_id"].astype(int)

    product_source = frame[
        frame["stock_code"].notna()
        & frame["description"].notna()
        & frame["unit_price"].gt(0)
    ].copy()
    product_source["product_id"], product_codes = pd.factorize(product_source["stock_code"], sort=True)
    product_source["product_id"] += 1
    product_map = dict(zip(product_codes.astype(str), range(1, len(product_codes) + 1), strict=True))
    products = (
        product_source.sort_values("invoice_date")
        .drop_duplicates("stock_code", keep="last")
        .assign(
            category=lambda data: data["description"].map(infer_category),
            unit_cost=lambda data: (data["unit_price"] * 0.65).round(2),
        )[["product_id", "description", "category", "unit_price", "unit_cost"]]
        .rename(columns={"description": "product_name"})
        .sort_values("product_id")
    )

    purchases = valid_customer[
        valid_customer["stock_code"].isin(product_map)
        & valid_customer["quantity"].ne(0)
        & valid_customer["unit_price"].gt(0)
    ].copy()
    purchases["product_id"] = purchases["stock_code"].map(product_map).astype(int)
    purchases["quantity_abs"] = purchases["quantity"].abs().astype(int)
    purchases["order_amount"] = (purchases["quantity_abs"] * purchases["unit_price"]).round(2)
    purchases["cost_amount"] = (purchases["order_amount"] * 0.65).round(2)
    purchases["transaction_id"] = np.arange(1, len(purchases) + 1)
    purchases["discount_amount"] = 0.0
    purchases["channel"] = "Online"
    purchases["status"] = np.where(purchases["is_cancelled"], "cancelled", "completed")
    transactions = purchases[
        [
            "transaction_id",
            "customer_id",
            "product_id",
            "quantity_abs",
            "order_amount",
            "cost_amount",
            "discount_amount",
            "invoice_date",
            "channel",
            "status",
        ]
    ].rename(columns={"quantity_abs": "quantity", "invoice_date": "order_date"})

    customer_source = valid_customer.sort_values("invoice_date")
    first_seen = customer_source.groupby("customer_id")["invoice_date"].min()
    country = customer_source.groupby("customer_id")["country"].agg(lambda values: values.mode().iloc[0] if not values.mode().empty else "Unknown")
    customers = pd.DataFrame({"customer_id": first_seen.index})
    customers["name"] = customers["customer_id"].map(lambda value: f"Customer {value}")
    customers["age"] = pd.NA
    customers["gender"] = "Unknown"
    customers["city"] = pd.NA
    customers["state"] = customers["customer_id"].map(country).fillna("Unknown")
    customers["signup_date"] = customers["customer_id"].map(first_seen).dt.date
    customers["email"] = pd.NA
    customers["is_active"] = True
    customers["created_at"] = customers["customer_id"].map(first_seen)

    completed = purchases[~purchases["is_cancelled"]].copy()
    monthly = (
        completed.set_index("invoice_date")
        .resample("MS")
        .agg(revenue=("order_amount", "sum"), orders=("invoice", "nunique"), units=("quantity_abs", "sum"))
        .reset_index()
    )
    return {
        "customers": customers,
        "products": products,
        "transactions": transactions,
        "monthly_summary": monthly,
    }


def infer_category(description: str) -> str:
    text = str(description).upper()
    categories = {
        "Home & Living": ("CANDLE", "HOLDER", "FRAME", "CLOCK", "CUSHION", "LAMP", "MIRROR"),
        "Kitchen & Dining": ("MUG", "CUP", "PLATE", "BOWL", "TEA", "KITCHEN", "CUTLERY"),
        "Bags & Accessories": ("BAG", "PURSE", "WALLET", "UMBRELLA"),
        "Stationery": ("CARD", "NOTEBOOK", "PENCIL", "PEN ", "PAPER", "STICKER"),
        "Seasonal & Gifts": ("CHRISTMAS", "HEART", "GIFT", "BIRTHDAY", "EASTER", "DECORATION"),
        "Kids & Toys": ("TOY", "DOLL", "CHILD", "BABY", "GAME"),
    }
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def save_outputs(tables: dict[str, pd.DataFrame], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_parquet(output / f"{name}.parquet", index=False)
    summary = pd.DataFrame(
        [{"table": name, "rows": len(frame), "columns": len(frame.columns)} for name, frame in tables.items()]
    )
    summary.to_csv(output / "dataset_summary.csv", index=False)


def load_database(tables: dict[str, pd.DataFrame], database_url: str) -> None:
    engine = create_engine(database_url)
    sys.path.insert(0, str(ROOT / "backend"))
    import app.db.models  # noqa: F401
    from app.db.base import Base

    Base.metadata.create_all(engine)
    for table in ("support_tickets", "marketing_activities", "transactions", "products", "customers"):
        with engine.begin() as connection:
            connection.exec_driver_sql(f"DELETE FROM {table}")
    tables["customers"].to_sql("customers", engine, if_exists="append", index=False, chunksize=10_000)
    tables["products"].to_sql("products", engine, if_exists="append", index=False, chunksize=10_000)
    tables["transactions"].to_sql("transactions", engine, if_exists="append", index=False, chunksize=25_000)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--database-url", help="Optional SQLAlchemy URL for loading prepared tables.")
    args = parser.parse_args()
    if not args.source.exists():
        raise FileNotFoundError(f"Dataset not found: {args.source}")
    raw = read_source(args.source)
    tables = prepare(raw)
    save_outputs(tables, args.output)
    if args.database_url:
        load_database(tables, args.database_url)
    print({name: len(frame) for name, frame in tables.items()})


if __name__ == "__main__":
    main()
