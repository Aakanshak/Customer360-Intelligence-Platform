from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.customer import ForecastRequest, SeedRequest
from app.services.analytics import dashboard_data, executive_kpis, exploratory_analytics, rfm_segmentation
from app.services.customer360 import build_customer360
from app.services.ml import churn_predictions, revenue_forecast, train_churn_models
from app.services.seed import seed_demo_data

router = APIRouter(tags=["Analytics and ML"])


@router.get("/kpis/executive")
def kpis(db: Session = Depends(get_db)):
    return executive_kpis(db)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return dashboard_data(db)


@router.get("/analytics/eda")
def eda(db: Session = Depends(get_db)):
    return exploratory_analytics(db)


@router.post("/churn/train")
def train_churn(db: Session = Depends(get_db)):
    return train_churn_models(db)


@router.get("/churn/predictions")
def predict_churn(db: Session = Depends(get_db)):
    return churn_predictions(db)


@router.post("/forecast/revenue")
def forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    return revenue_forecast(db, request.horizon)


@router.post("/admin/seed", tags=["Administration"])
def seed(request: SeedRequest, db: Session = Depends(get_db)):
    return seed_demo_data(db, request.customer_count, request.seed)


@router.get("/exports/customer360.csv", tags=["Exports"])
def export_customer360(db: Session = Depends(get_db)):
    frame = rfm_segmentation(build_customer360(db))
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customer360.csv"},
    )
