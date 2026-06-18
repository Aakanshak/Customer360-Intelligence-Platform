from pydantic import BaseModel, Field


class ChurnTrainingResponse(BaseModel):
    best_model: str
    metrics: dict[str, dict[str, float]]
    run_id: str


class ForecastRequest(BaseModel):
    horizon: int = Field(default=6, ge=1, le=24)


class SeedRequest(BaseModel):
    customer_count: int = Field(default=250, ge=20, le=5000)
    seed: int = 42
