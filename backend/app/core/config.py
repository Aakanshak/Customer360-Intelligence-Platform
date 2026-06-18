"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    project_name: str = os.getenv("PROJECT_NAME", "Customer360 Intelligence Platform")
    api_env: str = os.getenv("API_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./customer360.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    churn_days: int = int(os.getenv("CHURN_DAYS", "90"))
    forecast_horizon: int = int(os.getenv("FORECAST_HORIZON", "6"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "25"))


settings = Settings()
