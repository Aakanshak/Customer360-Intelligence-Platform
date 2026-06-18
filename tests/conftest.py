import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
TEST_DB = ROOT / "test_customer360.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["API_ENV"] = "test"

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.seed import seed_demo_data


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_demo_data(session, customer_count=80, seed=7)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db():
    with SessionLocal() as session:
        yield session
