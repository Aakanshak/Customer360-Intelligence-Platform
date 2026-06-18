# Data flow

1. A user uploads a customer, product, transaction, marketing, or support dataset.
2. The ingestion service normalizes headers, validates required fields, corrects types, removes key duplicates, profiles quality, and writes an ingestion audit record.
3. The Customer 360 service aggregates revenue, profit, frequency, recency, marketing, support, tenure, and product diversity.
4. Analytics services calculate RFM segments, CLV, cohorts, product/geographic summaries, health scores, and next-best actions.
5. ML services compare churn classifiers and generate lag-based revenue forecasts with validation metrics.
6. FastAPI exposes these products to Streamlit, Power BI, and other consumers.
