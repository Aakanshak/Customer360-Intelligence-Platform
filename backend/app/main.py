"""Customer360 Intelligence Platform API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.core.config import settings
from app.core.exceptions import Customer360Error
from app.core.logging import configure_logging
from app.db.init_db import init_db

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("application_started environment=%s", settings.api_env)
    yield
    logger.info("application_stopped")


app = FastAPI(
    title=settings.project_name,
    description="Unified customer analytics, segmentation, CLV, churn, forecasting, KPIs, and recommendations.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(Customer360Error)
async def domain_error_handler(_: Request, exc: Customer360Error):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health", tags=["Operations"])
def health_check():
    return {"status": "healthy", "environment": settings.api_env, "version": "1.0.0"}
