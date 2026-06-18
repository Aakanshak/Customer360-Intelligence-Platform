from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics import calculate_clv, cluster_customers, recommendations, rfm_segmentation
from app.services.customer360 import build_customer360, customer_profile

router = APIRouter(prefix="/customers", tags=["Customer 360"])


@router.get("/profile/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    profile = customer_profile(db, customer_id)
    if profile is None:
        raise HTTPException(404, "Customer not found.")
    return profile


@router.get("")
def list_customers(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    data = rfm_segmentation(calculate_clv(build_customer360(db)))
    if data.empty:
        return []
    columns = ["customer_id", "name", "state", "total_revenue", "order_count", "recency_days", "segment", "predicted_clv"]
    return data[columns].sort_values("total_revenue", ascending=False).head(limit).to_dict("records")


@router.get("/analytics/segments")
def segments(db: Session = Depends(get_db)):
    data = rfm_segmentation(build_customer360(db))
    return data[["customer_id", "name", "rfm_score", "segment"]].to_dict("records") if not data.empty else []


@router.get("/analytics/clusters")
def clusters(db: Session = Depends(get_db)):
    return cluster_customers(build_customer360(db))


@router.get("/analytics/clv")
def clv(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    data = calculate_clv(build_customer360(db))
    return data[["customer_id", "name", "predicted_clv", "clv_rank"]].sort_values("clv_rank").head(limit).to_dict("records") if not data.empty else []


@router.get("/analytics/recommendations")
def customer_recommendations(db: Session = Depends(get_db)):
    return recommendations(build_customer360(db))
