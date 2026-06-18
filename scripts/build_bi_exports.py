"""Generate governed flat-file exports for Excel and Power BI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from frontend.cloud_service import customer_master, dashboard, recommendations, source_tables  # noqa: E402


def main() -> None:
    output = ROOT / "exports" / "powerbi"
    output.mkdir(parents=True, exist_ok=True)
    customers, products, transactions = source_tables()
    master = customer_master()
    dashboard_data = dashboard()
    recs = pd.DataFrame(recommendations())

    master.to_csv(output / "customer360.csv", index=False)
    pd.DataFrame(dashboard_data["monthly_revenue"]).to_csv(output / "monthly_revenue.csv", index=False)
    pd.DataFrame(dashboard_data["segments"]).to_csv(output / "segments.csv", index=False)
    pd.DataFrame(dashboard_data["geography"]).to_csv(output / "geography.csv", index=False)
    pd.DataFrame(dashboard_data["category_revenue"]).to_csv(output / "category_revenue.csv", index=False)
    recs.to_csv(output / "recommendations.csv", index=False)
    products.to_csv(output / "products.csv", index=False)

    workbook_payload = {
        "dataset": dashboard_data["dataset"],
        "kpis": dashboard_data["kpis"],
        "monthly": dashboard_data["monthly_revenue"],
        "segments": dashboard_data["segments"],
        "geography": sorted(dashboard_data["geography"], key=lambda row: row["revenue"], reverse=True)[:20],
        "categories": dashboard_data["category_revenue"],
        "recommendations": recs.head(100).to_dict("records"),
        "data_dictionary": [
            ["customer_id", "Unique anonymized customer identifier", "UCI Customer ID"],
            ["total_revenue", "Completed transaction revenue", "Quantity × Price"],
            ["total_profit", "Demonstrative gross profit", "Revenue less estimated 65% cost"],
            ["recency_days", "Days since last purchase at dataset snapshot", "Derived"],
            ["order_count", "Distinct transaction-line count", "Derived"],
            ["segment", "RFM business segment", "Derived"],
            ["predicted_clv", "Three-year expected customer value", "Derived"],
            ["churn_probability", "Behavioral retention-risk score", "Derived"],
        ],
    }
    (output / "workbook_payload.json").write_text(json.dumps(workbook_payload, indent=2), encoding="utf-8")
    print({
        "customers": len(customers),
        "products": len(products),
        "transactions": len(transactions),
        "recommendations": len(recs),
    })


if __name__ == "__main__":
    main()
