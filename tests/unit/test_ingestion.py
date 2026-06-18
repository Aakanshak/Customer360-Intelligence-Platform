import pandas as pd
import pytest
from app.core.exceptions import DataValidationError
from app.services.ingestion import clean_and_validate, profile_data


def test_customer_cleaning_standardizes_and_deduplicates():
    frame = pd.DataFrame([
        {"customer_id": 1, "name": "  aDITI sharma", "age": 150, "gender": "f", "city": "mumbai", "state": "maharashtra", "signup_date": "2024-01-01"},
        {"customer_id": 1, "name": "Aditi Sharma", "age": 30, "gender": "Female", "city": "Mumbai", "state": "Maharashtra", "signup_date": "2024-01-01"},
    ])
    cleaned, report = clean_and_validate(frame, "customers")
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["name"] == "Aditi Sharma"
    assert report["duplicates_removed"] == 1


def test_missing_required_columns_raise_domain_error():
    with pytest.raises(DataValidationError):
        clean_and_validate(pd.DataFrame({"customer_id": [1]}), "customers")


def test_profile_reports_missing_and_duplicates():
    report = profile_data(pd.DataFrame({"a": [1, 1], "b": [None, None]}))
    assert report["row_count"] == 2
    assert report["duplicate_rows"] == 1
    assert report["missing_values"]["b"] == 2
