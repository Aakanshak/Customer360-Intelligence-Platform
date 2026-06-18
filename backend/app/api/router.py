from fastapi import APIRouter

from app.api import analytics, customer, ingestion

router = APIRouter(prefix="/api/v1")
router.include_router(ingestion.router)
router.include_router(customer.router)
router.include_router(analytics.router)
