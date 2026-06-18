# API reference

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Liveness and environment |
| POST | `/api/v1/admin/seed` | Create deterministic demo data |
| POST | `/api/v1/ingestion/files` | Validate and load CSV/Excel |
| GET | `/api/v1/customers` | Ranked Customer 360 list |
| GET | `/api/v1/customers/profile/{id}` | Individual unified profile |
| GET | `/api/v1/customers/analytics/segments` | RFM assignments |
| GET | `/api/v1/customers/analytics/clv` | CLV ranking |
| GET | `/api/v1/customers/analytics/recommendations` | Next-best actions |
| GET | `/api/v1/analytics/eda` | Demographic, cohort and product analysis |
| POST | `/api/v1/churn/train` | Compare and persist churn models |
| GET | `/api/v1/churn/predictions` | Customer risk scores |
| POST | `/api/v1/forecast/revenue` | Monthly forecast |
| GET | `/api/v1/dashboard` | Executive dashboard payload |
| GET | `/api/v1/exports/customer360.csv` | Power BI-ready export |
