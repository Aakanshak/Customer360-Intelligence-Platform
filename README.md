# Customer360 Intelligence Platform

A production-oriented customer analytics platform that unifies CRM, transaction, marketing, product, and support data into a governed Customer 360 layer. It delivers executive KPIs, segmentation, lifetime value, churn risk, revenue forecasts, cohort analysis, and explainable next-best actions through FastAPI and Streamlit.

## What it delivers

- Validated CSV and Excel ingestion with profiling, type correction, duplicate handling, audit batches, and checksum-based idempotency
- Unified customer master with revenue, profit, recency, frequency, product, campaign, support, and tenure features
- RFM segments: Platinum, Gold, Silver, and At-Risk
- K-Means customer clustering with silhouette diagnostics
- Three-year predicted CLV and customer ranking
- Logistic Regression, Random Forest, and optional XGBoost churn comparison
- Monthly revenue forecasting with lag features, MAE, RMSE, MAPE, and prediction intervals
- Executive, customer, sales, marketing, product, geographic, and cohort analytics
- Prioritized retention, loyalty, cross-sell, and campaign recommendations
- Seven analytical dashboard views plus governed data management
- PostgreSQL deployment, local SQLite mode, Docker, GitHub Actions, tests, logging, model artifacts, and Power BI export
- Included UCI Online Retail II preparation pipeline with 1,067,371 original transaction rows

## Architecture

```text
CSV / Excel / SQL
        |
        v
Validation + Quality Profiling
        |
        v
PostgreSQL / SQLite Operational Model
        |
        v
Customer 360 Feature Layer
     /        |          \
Analytics   ML Models   KPI/Rules
     \        |          /
          FastAPI
          /     \
 Streamlit     Power BI
```

See [architecture documentation](docs/architecture/architecture.md) and [data flow](docs/architecture/data-flow.md).

## Quick start with Docker

Prerequisites: Docker Desktop and Docker Compose.

```bash
docker compose up --build
```

Then open:

- Dashboard: http://localhost:8501
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

In the dashboard, open **Data Management** and select **Create demo dataset**.

For a Streamlit-only local run using the bundled public data:

```bash
streamlit run frontend/app.py
```

## Live deployment

The repository is prepared for Streamlit Community Cloud:

- Main file: `frontend/app.py`
- Dependency file: `requirements.txt`
- Data mode: bundled Parquet analytics assets
- External API required: no

See the [deployment guide](docs/deployment.md).

## Local development

Python 3.12 is recommended.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

Start the API:

```bash
cd backend
python -m scripts.seed_demo
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
streamlit run app.py
```

Local mode uses `backend/customer360.db`. Set `DATABASE_URL` to switch databases.

## Source datasets

### Included large public dataset

The project includes UCI **Online Retail II**:

- 1,067,371 original transaction records
- December 1, 2009 through December 9, 2011
- 5,942 identifiable customers after preparation
- 824,293 valid customer-linked transaction lines after quality filtering
- CC BY 4.0 license
- DOI: https://doi.org/10.24432/C5CG6D

Regenerate the analysis-ready Parquet tables:

```bash
python scripts/prepare_uci_retail.py
```

Load them into a local Customer360 database:

```bash
python scripts/prepare_uci_retail.py --database-url sqlite:///backend/customer360.db
```

The downloaded workbook is ignored by Git because of its size. Attribution and source details are preserved in `data/external/uci_online_retail_ii/README.md`.

The ingestion API accepts these dataset types:

| Type | Required fields |
|---|---|
| customers | customer_id, name, signup_date |
| products | product_id, product_name, category, unit_price, unit_cost |
| transactions | transaction_id, customer_id, order_amount, order_date |
| marketing | campaign_id, customer_id, touched_at |
| support | ticket_id, customer_id, opened_at |

Additional recognized columns are documented in the [data dictionary](docs/data_dictionary/data-dictionary.md).

Example upload:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/files ^
  -F "dataset_type=customers" ^
  -F "file=@data/sample/customers.csv"
```

## Key API routes

- `GET /api/v1/dashboard`
- `GET /api/v1/customers/profile/{customer_id}`
- `GET /api/v1/customers/analytics/segments`
- `GET /api/v1/customers/analytics/clv`
- `POST /api/v1/churn/train`
- `GET /api/v1/churn/predictions`
- `POST /api/v1/forecast/revenue`
- `GET /api/v1/customers/analytics/recommendations`
- `GET /api/v1/exports/customer360.csv`

See the complete [API reference](docs/api/api-reference.md).

## Testing

```bash
pip install -r backend/requirements.txt
pytest
```

The suite covers ingestion quality, Customer 360 calculations, RFM, CLV, KPIs, recommendations, APIs, forecasting, and an end-to-end executive-to-actionable-customer journey.

## Project structure

```text
backend/       FastAPI, SQLAlchemy, analytics and ML services
frontend/      Streamlit dashboard
database/      PostgreSQL DDL, indexes, and analytical SQL
analytics/     Analytics-domain documentation
ml/            ML-domain documentation and artifact conventions
tests/         Unit, integration, and end-to-end tests
docs/          Architecture, API, data dictionary, Power BI guide
data/          Sample, raw, and processed data zones
notebooks/     Exploration workspace
.github/       CI pipeline
```

## Model governance

- Churn definition: no completed purchase in more than 90 days
- Time and deterministic splits are preferred; random fallback is used only when a small demo test set lacks both classes
- Model comparison uses accuracy, precision, recall, F1, and ROC AUC
- Selected models are stored under `artifacts/`; run metadata and metrics are stored in `model_runs`
- Forecasting uses chronological validation and reports MAE, RMSE, and MAPE
- Recommendations always include a business reason and expected-value proxy

## Resume-ready description

> Designed and built an end-to-end Customer360 intelligence platform using Python, FastAPI, SQLAlchemy, PostgreSQL, Scikit-learn, XGBoost, Plotly, Streamlit, Docker, and GitHub Actions. Implemented governed multi-source ingestion, Customer 360 feature engineering, RFM/K-Means segmentation, CLV, churn modelling, revenue forecasting, KPI analytics, next-best-action recommendations, REST APIs, executive dashboards, Power BI exports, automated testing, and model lineage.

## Documentation

- [Architecture](docs/architecture/architecture.md)
- [Data flow](docs/architecture/data-flow.md)
- [API reference](docs/api/api-reference.md)
- [Data dictionary](docs/data_dictionary/data-dictionary.md)
- [Power BI integration](docs/power-bi-integration.md)

Screenshot placeholders can be added under `docs/screenshots/` after deployment.
