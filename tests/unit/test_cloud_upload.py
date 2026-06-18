import pandas as pd

from frontend.app import validate_and_standardize_upload


def test_cloud_upload_standardizes_and_reports_quality():
    frame = pd.DataFrame(
        [
            {"customer_id": 1, "name": "  aditi sharma ", "signup_date": "2025-01-01"},
            {"customer_id": 1, "name": "Aditi Sharma", "signup_date": "2025-01-01"},
        ]
    )
    cleaned, report = validate_and_standardize_upload(frame, "customers")
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["name"] == "Aditi Sharma"
    assert report["duplicates_removed"] == 1
