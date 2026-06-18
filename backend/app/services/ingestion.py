"""Validated, idempotent CSV/Excel ingestion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DataValidationError
from app.db.models import Customer, IngestionBatch, MarketingActivity, Product, SupportTicket, Transaction

MODEL_CONFIG: dict[str, tuple[type, list[str], dict[str, str]]] = {
    "customers": (
        Customer,
        ["customer_id", "name", "signup_date"],
        {"signup_date": "date", "created_at": "datetime", "is_active": "bool"},
    ),
    "products": (
        Product,
        ["product_id", "product_name", "category", "unit_price", "unit_cost"],
        {},
    ),
    "transactions": (
        Transaction,
        ["transaction_id", "customer_id", "order_amount", "order_date"],
        {"order_date": "datetime"},
    ),
    "marketing": (
        MarketingActivity,
        ["campaign_id", "customer_id", "touched_at"],
        {"touched_at": "datetime", "campaign_response": "bool"},
    ),
    "support": (
        SupportTicket,
        ["ticket_id", "customer_id", "opened_at"],
        {"opened_at": "datetime", "closed_at": "datetime"},
    ),
}


def load_bytes(content: bytes, filename: str) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    from io import BytesIO

    if suffix == ".csv":
        return pd.read_csv(BytesIO(content))
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(BytesIO(content))
    raise DataValidationError("Only CSV, XLS, and XLSX files are supported.")


def profile_data(df: pd.DataFrame) -> dict[str, Any]:
    numeric = df.select_dtypes(include="number")
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values": {k: int(v) for k, v in df.isna().sum().items()},
        "data_types": {k: str(v) for k, v in df.dtypes.items()},
        "numeric_summary": json.loads(numeric.describe().round(2).to_json()) if not numeric.empty else {},
    }


def clean_and_validate(df: pd.DataFrame, dataset_type: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    if dataset_type not in MODEL_CONFIG:
        raise DataValidationError(f"Unknown dataset type: {dataset_type}")
    _, required, conversions = MODEL_CONFIG[dataset_type]
    cleaned = df.copy()
    cleaned.columns = cleaned.columns.str.strip().str.lower().str.replace(" ", "_")
    missing = sorted(set(required) - set(cleaned.columns))
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(missing)}")

    before = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=[required[0]], keep="last")
    for column, conversion in conversions.items():
        if column not in cleaned:
            continue
        if conversion in {"date", "datetime"}:
            cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")
            if conversion == "date":
                cleaned[column] = cleaned[column].dt.date
        elif conversion == "bool":
            cleaned[column] = cleaned[column].map(
                lambda value: str(value).strip().lower() in {"1", "true", "yes", "y"}
            )

    for col in ("name", "city", "state", "product_name", "category"):
        if col in cleaned:
            cleaned[col] = cleaned[col].astype("string").str.strip().str.title()
    if "gender" in cleaned:
        cleaned["gender"] = cleaned["gender"].astype("string").str.strip().str.title().replace({"M": "Male", "F": "Female"})
    if "age" in cleaned:
        cleaned.loc[~cleaned["age"].between(16, 110), "age"] = pd.NA
        cleaned["age"] = cleaned["age"].fillna(cleaned["age"].median()).round().astype(int)
    for col in ("order_amount", "cost_amount", "discount_amount", "unit_price", "unit_cost", "campaign_cost"):
        if col in cleaned:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce").fillna(0).clip(lower=0)

    invalid_required = {col: int(cleaned[col].isna().sum()) for col in required if cleaned[col].isna().any()}
    if invalid_required:
        raise DataValidationError(f"Invalid required values: {invalid_required}")
    report = profile_data(cleaned)
    report["duplicates_removed"] = before - len(cleaned)
    return cleaned, report


def ingest_dataframe(db: Session, df: pd.DataFrame, dataset_type: str, filename: str, checksum: str) -> dict[str, Any]:
    existing = db.scalar(select(IngestionBatch).where(IngestionBatch.checksum == checksum))
    if existing:
        return {"status": "duplicate", "batch_id": existing.batch_id, "rows_loaded": existing.row_count}

    cleaned, report = clean_and_validate(df, dataset_type)
    model, _, _ = MODEL_CONFIG[dataset_type]
    allowed = {column.name for column in model.__table__.columns}
    records = [{key: _python_value(value) for key, value in row.items() if key in allowed} for row in cleaned.to_dict("records")]
    primary_key = next(iter(model.__table__.primary_key.columns)).name
    for record in records:
        current = db.get(model, record[primary_key])
        if current:
            for key, value in record.items():
                setattr(current, key, value)
        else:
            db.add(model(**record))

    batch = IngestionBatch(
        batch_id=str(uuid4()),
        dataset_type=dataset_type,
        file_name=filename,
        checksum=checksum,
        row_count=len(records),
        status="completed",
        quality_report=json.dumps(report, default=str),
    )
    db.add(batch)
    db.commit()
    return {"status": "completed", "batch_id": batch.batch_id, "rows_loaded": len(records), "quality_report": report}


def checksum_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _python_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value
