"""Trainable churn and revenue forecasting services."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientDataError
from app.db.models import ModelRun, Transaction
from app.services.customer360 import build_customer360, table_frame

ARTIFACT_DIR = Path("artifacts")
CHURN_FEATURES = [
    "age", "gender", "state", "tenure_days", "order_count", "total_revenue",
    "average_order_value", "product_diversity", "campaign_response_rate",
    "support_tickets", "avg_resolution_hours", "avg_satisfaction",
]


def train_churn_models(db: Session) -> dict:
    data = build_customer360(db)
    if len(data) < 20 or (data["order_count"] > 0).sum() < 10:
        raise InsufficientDataError("At least 20 customers and 10 purchasing customers are required.")
    data = data.copy()
    data["churned"] = (data["recency_days"] > 90).astype(int)
    if data.churned.nunique() < 2:
        raise InsufficientDataError("Training data must contain both churned and retained customers.")

    data = data.sort_values("signup_date")
    split = max(int(len(data) * 0.75), 1)
    train, test = data.iloc[:split], data.iloc[split:]
    if test.churned.nunique() < 2:
        train, test = data.sample(frac=0.75, random_state=42), data.drop(data.sample(frac=0.75, random_state=42).index)

    numeric = [col for col in CHURN_FEATURES if col not in {"gender", "state"}]
    categorical = ["gender", "state"]
    preprocess = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ])
    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=250, max_depth=8, class_weight="balanced", random_state=42),
    }
    try:
        from xgboost import XGBClassifier
        candidates["xgboost"] = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=42)
    except ImportError:
        pass

    results: dict[str, dict] = {}
    fitted: dict[str, Pipeline] = {}
    for name, estimator in candidates.items():
        pipeline = Pipeline([("preprocess", preprocess), ("model", estimator)])
        pipeline.fit(train[CHURN_FEATURES], train["churned"])
        predictions = pipeline.predict(test[CHURN_FEATURES])
        probabilities = pipeline.predict_proba(test[CHURN_FEATURES])[:, 1]
        results[name] = {
            "accuracy": round(float(accuracy_score(test.churned, predictions)), 4),
            "precision": round(float(precision_score(test.churned, predictions, zero_division=0)), 4),
            "recall": round(float(recall_score(test.churned, predictions, zero_division=0)), 4),
            "f1": round(float(f1_score(test.churned, predictions, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(test.churned, probabilities)), 4),
        }
        fitted[name] = pipeline
    best_name = max(results, key=lambda name: results[name]["roc_auc"])
    ARTIFACT_DIR.mkdir(exist_ok=True)
    path = ARTIFACT_DIR / "churn_model.joblib"
    joblib.dump({"pipeline": fitted[best_name], "features": CHURN_FEATURES, "trained_at": datetime.utcnow().isoformat()}, path)
    run = ModelRun(
        run_id=str(uuid4()), model_type="churn", model_name=best_name, version=datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        metrics_json=json.dumps(results), artifact_path=str(path),
    )
    db.add(run)
    db.commit()
    return {"best_model": best_name, "metrics": results, "run_id": run.run_id}


def churn_predictions(db: Session) -> list[dict]:
    data = build_customer360(db)
    if data.empty:
        return []
    path = ARTIFACT_DIR / "churn_model.joblib"
    if path.exists():
        bundle = joblib.load(path)
        probabilities = bundle["pipeline"].predict_proba(data[bundle["features"]])[:, 1]
    else:
        probabilities = np.clip(
            0.15 + (data.recency_days / 365).clip(0, 1) * 0.65 + (data.support_tickets > 2) * 0.1 - data.campaign_response_rate * 0.15,
            0.01, 0.99,
        )
    output = data[["customer_id", "name"]].copy()
    output["churn_probability"] = np.round(probabilities, 4)
    output["risk_level"] = pd.cut(output.churn_probability, [0, 0.35, 0.65, 1], labels=["Low", "Medium", "High"], include_lowest=True).astype(str)
    return output.sort_values("churn_probability", ascending=False).to_dict("records")


def revenue_forecast(db: Session, horizon: int = 6) -> dict:
    transactions = table_frame(db, Transaction)
    if transactions.empty:
        return {"history": [], "forecast": [], "metrics": {}}
    transactions["order_date"] = pd.to_datetime(transactions.order_date)
    monthly = transactions.set_index("order_date").resample("MS")["order_amount"].sum().asfreq("MS", fill_value=0)
    history = [{"month": index.strftime("%Y-%m"), "revenue": round(float(value), 2)} for index, value in monthly.items()]
    if len(monthly) < 8:
        baseline = float(monthly.tail(min(3, len(monthly))).mean())
        future_index = pd.date_range(monthly.index.max() + pd.offsets.MonthBegin(), periods=horizon, freq="MS")
        forecast = [{"month": index.strftime("%Y-%m"), "forecast": round(baseline, 2), "lower": round(baseline * 0.8, 2), "upper": round(baseline * 1.2, 2)} for index in future_index]
        return {"history": history, "forecast": forecast, "metrics": {"model": "moving_average", "mae": None, "rmse": None, "mape": None}}

    frame = pd.DataFrame({"target": monthly})
    for lag in (1, 2, 3, 6):
        frame[f"lag_{lag}"] = frame.target.shift(lag)
    frame["rolling_3"] = frame.target.shift(1).rolling(3).mean()
    frame["month"] = frame.index.month
    train = frame.dropna()
    features = [col for col in train.columns if col != "target"]
    split = max(len(train) - max(2, len(train) // 4), 1)
    model = GradientBoostingRegressor(random_state=42, n_estimators=150, learning_rate=0.05)
    model.fit(train.iloc[:split][features], train.iloc[:split].target)
    validation = train.iloc[split:]
    predictions = model.predict(validation[features]) if len(validation) else np.array([])
    metrics = {"model": "gradient_boosting", "mae": None, "rmse": None, "mape": None}
    if len(validation):
        metrics.update({
            "mae": round(float(mean_absolute_error(validation.target, predictions)), 2),
            "rmse": round(float(mean_squared_error(validation.target, predictions) ** 0.5), 2),
            "mape": round(float(np.mean(np.abs((validation.target - predictions) / validation.target.replace(0, np.nan))) * 100), 2),
        })
    model.fit(train[features], train.target)
    extended = monthly.copy()
    forecast = []
    for _ in range(horizon):
        next_date = extended.index.max() + pd.offsets.MonthBegin()
        feature_row = pd.DataFrame([{
            "lag_1": extended.iloc[-1], "lag_2": extended.iloc[-2], "lag_3": extended.iloc[-3],
            "lag_6": extended.iloc[-6], "rolling_3": extended.iloc[-3:].mean(), "month": next_date.month,
        }], columns=features)
        value = max(float(model.predict(feature_row)[0]), 0)
        error = metrics["rmse"] or value * 0.15
        forecast.append({"month": next_date.strftime("%Y-%m"), "forecast": round(value, 2), "lower": round(max(0, value - 1.96 * error), 2), "upper": round(value + 1.96 * error, 2)})
        extended.loc[next_date] = value
    return {"history": history, "forecast": forecast, "metrics": metrics}
