from app.services.analytics import calculate_clv, executive_kpis, recommendations, rfm_segmentation
from app.services.customer360 import build_customer360


def test_customer360_and_rfm_are_complete(db):
    master = build_customer360(db)
    segmented = rfm_segmentation(master)
    assert len(master) == 80
    assert {"total_revenue", "recency_days", "campaign_response_rate"}.issubset(master.columns)
    assert segmented.segment.isin(["Platinum", "Gold", "Silver", "At-Risk"]).all()


def test_clv_is_non_negative_and_ranked(db):
    clv = calculate_clv(build_customer360(db))
    assert (clv.predicted_clv >= 0).all()
    assert clv.clv_rank.min() == 1


def test_kpis_and_recommendations_are_business_ready(db):
    kpis = executive_kpis(db)
    recs = recommendations(build_customer360(db))
    assert kpis["customers"] == 80
    assert kpis["revenue"] > 0
    assert all({"customer_id", "action", "reason", "priority", "expected_value"} <= item.keys() for item in recs)
