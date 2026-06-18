# Customer360 Intelligence Platform — Interview Preparation Guide

This guide explains how the project was built, why each technology was selected, the problems encountered during development and deployment, and how to discuss the work confidently in an interview.

---

## 1. Project summary

Customer360 Intelligence Platform is an end-to-end customer analytics solution that consolidates customer, transaction, product, marketing, and support information into a unified analytical layer.

It provides:

- Governed CSV and Excel ingestion
- Data validation, cleaning, profiling, and standardization
- Customer 360 feature engineering
- Exploratory and cohort analysis
- RFM and K-Means customer segmentation
- Customer Lifetime Value estimation
- Churn-risk scoring and model comparison
- Monthly revenue forecasting
- Executive KPI calculations
- Next-best-action recommendations
- FastAPI services
- An interactive Streamlit dashboard
- PostgreSQL and SQLite support
- Power BI and Excel-ready exports
- Docker, GitHub Actions, testing, and Streamlit Cloud deployment

### Live links

- Application: https://customer360-intelligence-platform.streamlit.app
- Repository: https://github.com/Aakanshak/Customer360-Intelligence-Platform

### Dataset

The deployed application uses UCI Online Retail II:

- 1,067,371 original rows
- 824,293 prepared customer-linked transaction rows
- 5,942 customers
- 4,931 products
- 41 geographic markets
- Data period: December 2009 to December 2011
- License: CC BY 4.0

---

## 2. One-minute interview explanation

> I built a production-oriented Customer360 analytics platform that transforms raw retail transactions into customer-level business intelligence. I used Python and Pandas for data preparation, SQLAlchemy with PostgreSQL and SQLite for persistence, Scikit-learn and XGBoost for customer modelling, FastAPI for APIs, and Streamlit and Plotly for the user interface. The platform performs RFM segmentation, CLV calculation, churn-risk analysis, revenue forecasting, KPI reporting, and next-best-action recommendations. I also created Power BI and Excel-ready analytical exports, containerized the application with Docker, added automated testing through GitHub Actions, and deployed a self-contained version on Streamlit Community Cloud. The deployed version analyzes over 824,000 prepared transactions.

---

## 3. Thirty-second elevator pitch

> Customer360 is an end-to-end analytics platform that converts fragmented customer and transaction data into segments, CLV, churn risk, forecasts, KPIs, and recommendations. It processes more than 824,000 prepared transaction rows and exposes the results through a polished Streamlit dashboard, FastAPI services, and Power BI/Excel exports. I built the complete data, analytics, ML, software-engineering, testing, and deployment workflow.

---

## 4. Business problem

Organizations commonly store customer information in separate systems:

- CRM
- Sales and transaction systems
- Marketing platforms
- Customer support systems
- Product catalogues

This creates several problems:

- Business teams cannot see one complete customer profile.
- Different reports calculate the same KPI differently.
- High-value customers are difficult to identify.
- Churn is discovered after revenue has already been lost.
- Campaign targeting is broad instead of customer-specific.
- Forecasts and executive reports are disconnected from the underlying customer behavior.

Customer360 solves this by creating a governed customer-level analytical layer shared by APIs, dashboards, ML models, Power BI, and Excel.

---

## 5. Project architecture

```text
CSV / Excel / Public Dataset / SQL
                 |
                 v
       Ingestion and validation
                 |
                 v
       Operational data model
    Customers / Products / Transactions
       Marketing / Support / Audits
                 |
                 v
      Customer 360 feature layer
                 |
       +---------+---------+
       |         |         |
       v         v         v
 Analytics   ML models   KPI engine
 RFM / CLV   Churn       Recommendations
 Cohorts     Forecasting Health score
       |         |         |
       +---------+---------+
                 |
                 v
              FastAPI
                 |
       +---------+----------+
       |                    |
       v                    v
  Streamlit          Power BI / Excel
```

### Architectural style

The local version is a modular service-oriented application:

- The database is the system of record.
- Business calculations live in reusable service modules.
- FastAPI exposes versioned endpoints.
- Streamlit consumes the API.
- Power BI and Excel consume governed exports.

The Streamlit Cloud deployment is self-contained:

- It reads committed Parquet analytical assets.
- It does not require a separately hosted API.
- Uploads are processed in the user's Streamlit session.
- Cloud uploads are temporary because free Streamlit Cloud storage is ephemeral.

---

## 6. Technology choices

| Technology | Purpose | Why it was selected |
|---|---|---|
| Python | Primary implementation language | Strong data, API, ML, and automation ecosystem |
| Pandas | Transformation and analysis | Efficient tabular operations and broad file support |
| NumPy | Numerical operations | Vectorized calculations and statistical support |
| SQLAlchemy | Database access | Database-independent ORM and SQL abstraction |
| PostgreSQL | Production database | Reliability, indexing, constraints, and analytical SQL |
| SQLite | Local development and tests | Zero-configuration development |
| FastAPI | REST API | Type-aware, fast, automatic OpenAPI documentation |
| Pydantic | Request validation | Reliable API contracts |
| Scikit-learn | ML and preprocessing | Pipelines, models, scaling, and metrics |
| XGBoost | Advanced churn model | Strong performance on structured tabular data |
| Plotly | Interactive visualizations | Rich hover, filters, and dashboard charts |
| Streamlit | Analytics frontend | Rapid Python-native analytical application development |
| Parquet | Cloud analytical storage | Smaller and faster than CSV with preserved data types |
| Power BI | Enterprise reporting | Business-facing dashboards and DAX measures |
| Excel | Ad hoc analysis | Familiar interface and Power Query compatibility |
| Docker | Reproducible deployment | Consistent backend, frontend, and database environments |
| GitHub Actions | CI | Automated linting, testing, and Docker validation |
| GitHub | Version control | Collaboration, portfolio presentation, and CI trigger |
| Streamlit Cloud | Public deployment | Simple GitHub-connected hosting |

---

## 7. End-to-end implementation

### Step 1: Requirement analysis

The original requirement described 15 modules but the proposed tables did not contain enough information to calculate everything.

Examples:

- Profit required cost data.
- Product and cross-sell analysis required product identifiers.
- Churn required an observable inactivity definition.
- Campaign effectiveness required campaign cost and dated responses.
- Cohorts required signup and activity dates.

The data model was expanded before model development.

### Step 2: Database design

Core entities:

- `customers`
- `products`
- `transactions`
- `marketing_activities`
- `support_tickets`
- `ingestion_batches`
- `model_runs`

Important design choices:

- Primary and foreign keys enforce relationships.
- Customer/date indexes support customer history queries.
- Product category indexes support category analysis.
- Ingestion checksums prevent duplicate file loads.
- Model-run records preserve model lineage and metrics.

### Step 3: Ingestion and cleaning

The ingestion service:

1. Accepts CSV, XLS, and XLSX.
2. Normalizes column names.
3. Validates required fields by dataset type.
4. Corrects date, numeric, Boolean, and text types.
5. Removes primary-key duplicates.
6. Handles invalid ages and negative monetary values.
7. Generates a quality report.
8. Uses a SHA-256 checksum for idempotency.
9. Updates existing records or inserts new records.

The Streamlit Cloud upload flow also:

- Displays required columns.
- Shows a standardized preview.
- Displays rows received, duplicates removed, missing values, and invalid required values.
- Allows the cleaned result to be downloaded.

### Step 4: Customer 360 feature engineering

Transaction, marketing, support, and customer data are aggregated to one row per customer.

Important features:

- Total revenue
- Total profit
- Order count
- Average order value
- First and last purchase date
- Recency
- Product diversity
- Purchase frequency
- Customer tenure
- Campaign response rate
- Marketing cost
- Support ticket count
- Average resolution time
- Satisfaction score

This master table is reused across segmentation, CLV, churn, KPIs, and recommendations.

### Step 5: Exploratory analysis

The platform calculates:

- Revenue trends
- Customer demographics
- Geographic contribution
- Product and category performance
- Cohort activity
- Segment distribution
- Customer value distribution

Production analytics are implemented in reusable services rather than only in notebooks.

### Step 6: RFM segmentation

RFM means:

- Recency: How recently did the customer purchase?
- Frequency: How often did the customer purchase?
- Monetary: How much revenue did the customer generate?

Each feature receives a quartile score from 1 to 4.

The combined score maps customers to:

- Platinum
- Gold
- Silver
- At-Risk

This approach is transparent and easy for business users to understand.

### Step 7: K-Means clustering

K-Means provides a second, data-driven segmentation view.

Process:

1. Select customer behavior features.
2. Replace invalid and missing values.
3. Apply `log1p` to reduce skew.
4. Standardize features.
5. Fit K-Means with a fixed random seed.
6. Evaluate separation using silhouette score.

RFM is business-rule-driven, while K-Means can reveal patterns not anticipated in the rules.

### Step 8: Customer Lifetime Value

The project uses an explainable CLV approximation based on:

- Average order value
- Annual purchase frequency
- Estimated margin
- Retention rate
- Discount rate
- Three-year horizon

Customers are ranked by predicted CLV.

This model is intentionally interpretable. A future enhancement could use BG/NBD and Gamma-Gamma models.

### Step 9: Churn modelling

Operational churn definition:

> A customer is considered churned when no completed purchase occurs for more than 90 days after the analytical snapshot.

Candidate models:

- Logistic Regression
- Random Forest
- XGBoost

Features include:

- Demographics
- Tenure
- Order count
- Revenue
- Average order value
- Product diversity
- Campaign response
- Support behavior

Metrics:

- Accuracy
- Precision
- Recall
- F1 score
- ROC AUC

Why multiple metrics?

- Accuracy can be misleading with class imbalance.
- Precision measures how many flagged customers truly churn.
- Recall measures how many churners were found.
- F1 balances precision and recall.
- ROC AUC measures ranking quality across thresholds.

### Step 10: Revenue forecasting

Monthly revenue is generated from completed transactions.

Features:

- Lag 1
- Lag 2
- Lag 3
- Lag 6
- Three-month rolling average
- Calendar month

The model uses Gradient Boosting in the deployed analytical service and reports:

- MAE
- RMSE
- MAPE
- Prediction intervals

Chronological validation is used because random splitting would leak future behavior into the past.

### Step 11: KPI engine

Centralized KPIs include:

- Customer count
- Active customer count
- Revenue
- Profit
- Average order value
- Churn rate
- Retention rate
- Revenue growth
- Campaign conversion
- Customer health score
- Top segment

Centralization prevents different dashboards from calculating conflicting values.

### Step 12: Recommendation engine

The recommendation engine combines transparent business rules with analytical features.

Examples:

- Retention outreach for inactive previous buyers
- VIP loyalty offers for Platinum customers
- Cross-sell recommendations for repeat customers with low product diversity
- Campaign targeting for historically responsive customers

Each recommendation contains:

- Customer ID
- Customer name
- Recommended action
- Business reason
- Priority
- Expected-value estimate

### Step 13: API development

Representative endpoints:

```text
GET  /health
POST /api/v1/ingestion/files
GET  /api/v1/customers/profile/{customer_id}
GET  /api/v1/customers/analytics/segments
GET  /api/v1/customers/analytics/clv
GET  /api/v1/churn/predictions
POST /api/v1/churn/train
POST /api/v1/forecast/revenue
GET  /api/v1/customers/analytics/recommendations
GET  /api/v1/dashboard
GET  /api/v1/exports/customer360.csv
```

FastAPI automatically provides OpenAPI documentation.

### Step 14: Dashboard development

Dashboard pages:

1. Executive Summary
2. Segmentation
3. Customer Lifetime Value
4. Churn Analytics
5. Revenue Forecast
6. Geography
7. Recommendations
8. Data Management

UI improvements:

- Dark enterprise theme
- Responsive KPI cards
- Branded navigation
- Interactive Plotly charts
- Business interpretation cards
- Source and date-range visibility
- Upload validation and cleaned-file download

### Step 15: Power BI and Excel

The project generates governed exports:

- `customer360.csv`
- `products.csv`
- `monthly_revenue.csv`
- `segments.csv`
- `geography.csv`
- `category_revenue.csv`
- `recommendations.csv`

Power BI can load these through the Text/CSV connector.

Excel can load the same files through:

```text
Data → Get Data → From Text/CSV
```

Suggested Power BI DAX measures are included in `docs/power-bi-measures.md`.

### Step 16: Testing and CI/CD

Testing covers:

- Cleaning and validation
- Duplicate handling
- Customer 360 construction
- RFM segmentation
- CLV calculations
- KPI generation
- Recommendations
- API endpoints
- Forecasting
- Streamlit Cloud rendering
- Cloud upload standardization

GitHub Actions runs:

1. Dependency installation
2. Ruff linting
3. Pytest and coverage
4. Docker Compose validation
5. Backend and frontend Docker builds

### Step 17: Deployment

The code was:

1. Committed to Git.
2. Published to a public GitHub repository.
3. Validated by GitHub Actions.
4. Connected to Streamlit Community Cloud.
5. Deployed using `frontend/app.py`.
6. Configured to use committed Parquet data without a separate API server.

---

## 8. STAR method: overall project

### Situation

Customer information was conceptually spread across transactions, customer records, products, marketing, and support systems. Decision-makers needed a unified view covering revenue, customer value, churn, forecasting, and recommended actions.

### Task

Design and implement a portfolio-quality enterprise analytics platform that covered the complete lifecycle from ingestion and data modelling to ML, dashboards, APIs, testing, BI exports, and deployment.

### Action

- Designed a normalized operational data model.
- Built validated and idempotent ingestion.
- Created a reusable Customer 360 feature layer.
- Implemented RFM, K-Means, CLV, churn, forecasting, KPIs, and recommendations.
- Exposed analytical capabilities through FastAPI.
- Designed an eight-page Streamlit dashboard.
- Prepared Power BI and Excel data marts.
- Added automated tests, Docker, and GitHub Actions.
- Adapted the application for Streamlit Cloud using Parquet assets.
- Deployed and monitored the public application.

### Result

- Processed 824,293 prepared transaction rows.
- Produced profiles for 5,942 customers.
- Analyzed 4,931 products and 41 markets.
- Created 4,500+ actionable recommendations.
- Achieved passing automated tests and CI.
- Completed a successful Docker build.
- Published a public GitHub repository and live Streamlit application.

---

## 9. STAR stories for major challenges

### Story 1: Incomplete data model

**Situation:** The initial requirement requested profit, product analysis, churn, campaigns, and cross-sell, but the proposed tables contained only basic customer and transaction fields.

**Task:** Make the analytics technically valid without producing misleading metrics.

**Action:** I mapped every requested output back to the required source data. I added product cost, quantity, category, channel, campaign cost, support satisfaction, signup dates, transaction status, ingestion audits, and model-run metadata.

**Result:** The platform could support the requested KPIs and models with a defensible schema rather than relying on hidden assumptions.

### Story 2: Large-data performance

**Situation:** The first large-data dashboard request took about 58 seconds because SQLAlchemy instantiated more than 824,000 ORM objects.

**Task:** Make the dashboard practical for interactive use.

**Action:** I replaced row-by-row ORM materialization with vectorized `pandas.read_sql_query`, reused loaded data between calculations, and avoided recalculating the same master table inside KPI functions.

**Result:** Dashboard generation improved from approximately 58 seconds to approximately 9 seconds on the local machine.

### Story 3: Historical churn was incorrect

**Situation:** The UCI dataset ended in 2011, while the application was running in 2026. Calculating recency against the current date classified every customer as churned.

**Task:** Make churn and retention meaningful for historical datasets.

**Action:** I changed the analytical snapshot from the current system date to one day after the maximum transaction date in the dataset.

**Result:** Churn and retention became relative to the dataset's observation period, producing usable customer-risk segmentation.

### Story 4: Streamlit Cloud import failure

**Situation:** The deployed application failed with `ModuleNotFoundError` because Streamlit executed `frontend/app.py` with a different import path than the local test environment.

**Task:** Support both local package execution and Streamlit's entrypoint execution.

**Action:** I added a dual import strategy that first imports `frontend.cloud_service` and falls back to `cloud_service`.

**Result:** The same code runs locally, in automated tests, and on Streamlit Community Cloud.

### Story 5: Missing cloud dependencies

**Situation:** Streamlit Cloud selected `frontend/requirements.txt` because the entrypoint was inside the `frontend` directory. That file initially lacked Scikit-learn and PyArrow.

**Task:** Ensure the cloud environment installed every package required by the self-contained analytics service.

**Action:** I added NumPy, Scikit-learn, PyArrow, and OpenPyXL to the frontend deployment manifest and verified it using a dependency dry run.

**Result:** The application could import ML components and read Parquet and Excel files in Streamlit Cloud.

### Story 6: Disabled upload feature

**Situation:** The cloud app displayed an upload widget but disabled it because cloud storage was treated as read-only.

**Task:** Provide a useful upload experience without pretending that free cloud storage was persistent.

**Action:** I enabled session-based CSV and Excel processing. The application validates schemas, standardizes data, reports quality, previews the result, and lets the user download the cleaned CSV. It explicitly explains that data disappears when the session ends.

**Result:** The upload workflow became functional and honest about cloud persistence limitations.

### Story 7: SQLite bulk-load limitation

**Situation:** Loading the prepared data with large multi-row SQL statements caused SQLite's “too many SQL variables” error.

**Task:** Load hundreds of thousands of rows reliably.

**Action:** I removed `method="multi"` for SQLite loading and used appropriately sized executemany chunks.

**Result:** All 824,293 prepared transaction records loaded successfully.

### Story 8: Partial initial scaffold

**Situation:** The workspace initially contained a small scaffold with outdated Pydantic usage, incomplete models, no working frontend, and limited endpoints.

**Task:** Convert it into one coherent, runnable system.

**Action:** I replaced incompatible configuration, upgraded the SQLAlchemy model style, created service boundaries, completed the API, added the dashboard, tests, deployment assets, documentation, and sample/public data pipelines.

**Result:** The project moved from a partial skeleton to a deployed end-to-end platform.

---

## 10. Interview questions and answers

### General project questions

#### 1. What problem does this project solve?

It creates one governed customer view from fragmented business data and converts it into segmentation, value, risk, forecasts, KPIs, and recommended actions.

#### 2. What makes it more than a dashboard?

The dashboard is only the presentation layer. The project includes ingestion, validation, database design, feature engineering, analytics, ML pipelines, APIs, tests, CI/CD, BI exports, and deployment.

#### 3. Why is it called Customer 360?

Because the analytical profile combines identity, transaction, product, marketing, and support signals into one customer-level record.

#### 4. Who would use the platform?

- Executives for KPIs and trends
- Marketing teams for targeting
- Customer-success teams for retention
- Sales teams for upsell and cross-sell
- Analysts for exploration
- Data scientists for reusable features

#### 5. What is the most important design decision?

Creating one reusable Customer 360 feature layer. It prevents each dashboard or model from independently rebuilding and redefining customer behavior.

### Data-engineering questions

#### 6. How do you validate uploaded files?

I normalize headers, check dataset-specific required fields, coerce types, validate required values, remove key duplicates, profile missing values, and return a quality report.

#### 7. How do you prevent loading the same file twice?

The backend computes a SHA-256 checksum and stores it in the ingestion audit table. A repeated checksum returns a duplicate status instead of loading the file again.

#### 8. How do you handle duplicates?

I deduplicate using the natural or primary identifier for each dataset type and retain the latest occurrence.

#### 9. How do you handle missing values?

The strategy depends on the field:

- Missing required identifiers or dates fail validation.
- Optional text remains unknown.
- Numeric analytical fields receive controlled defaults where appropriate.
- Age can be median-imputed after invalid ranges are converted to missing.

#### 10. How do you handle outliers?

Business-invalid values are corrected or rejected. For ML features, log transformations and scaling reduce skew. In a production extension, I would store outlier flags instead of silently deleting legitimate extreme customers.

#### 11. Why Parquet for deployment?

Parquet is compressed, typed, and significantly faster and smaller than CSV for analytical loading. The prepared transaction file is under 10 MB in Parquet despite containing more than 824,000 rows.

#### 12. Why PostgreSQL and SQLite?

PostgreSQL is appropriate for production constraints, concurrency, indexing, and deployment. SQLite provides quick local development and isolated tests without additional infrastructure.

#### 13. What indexes were created?

Indexes include customer/date transaction access, order date, customer state, product category, and relevant foreign keys.

#### 14. How would you scale ingestion further?

I would use:

- Object storage for raw files
- Background task queues
- Chunked validation
- Bulk PostgreSQL `COPY`
- Incremental transformations
- Airflow or Dagster orchestration
- Data-quality tools such as Great Expectations

### Analytics questions

#### 15. Explain RFM.

RFM scores customers according to recent purchasing, purchase frequency, and monetary contribution. It produces an interpretable value and engagement segmentation.

#### 16. Why use both RFM and K-Means?

RFM is transparent and business-friendly. K-Means is data-driven and can discover groups that do not match predefined score thresholds. They complement each other.

#### 17. What does CLV mean?

CLV estimates the future economic value of the customer relationship. It helps determine how much retention or service investment is economically sensible.

#### 18. What assumptions are in the CLV model?

- Three-year horizon
- Estimated margin rate
- Portfolio-level retention estimate
- Discount rate
- Future behavior broadly resembles historical behavior

These assumptions are explicit and can be replaced with business-specific values.

#### 19. How is customer health calculated?

It combines recency with available engagement and satisfaction indicators. The deployed UCI dataset lacks marketing and support fields, so its score relies primarily on transaction recency.

#### 20. How do you calculate retention?

At the analytical snapshot, customers with a purchase within 90 days are treated as retained. The retention rate is retained customers divided by total customers.

#### 21. Why is campaign conversion zero in the public deployment?

The UCI dataset contains transactions, products, customers, and countries but no campaign records. The platform does not fabricate campaign responses, so the KPI correctly remains zero.

#### 22. Why are customer names generic?

The source dataset provides customer IDs but no names. Generic labels preserve the source's anonymity instead of inventing personal details.

### Machine-learning questions

#### 23. How did you define churn?

No completed purchase for more than 90 days relative to the analytical snapshot.

#### 24. Why not use the current date for churn?

The dataset is historical. Using today's date would label every customer as churned. The correct snapshot is relative to the final observable transaction date.

#### 25. Why compare Logistic Regression, Random Forest, and XGBoost?

- Logistic Regression provides an interpretable baseline.
- Random Forest handles nonlinear relationships and interactions.
- XGBoost is a strong structured-data model.

Model comparison prevents selecting complexity without evidence.

#### 26. How did you avoid leakage?

The design uses behavioral features available at the analytical snapshot and chronological validation for time-dependent problems. A stronger production extension would generate multiple historical snapshots and future churn labels.

#### 27. What is class imbalance?

It occurs when churners and non-churners are not equally represented. Accuracy can then hide poor churn detection. Class weights and precision/recall metrics help address it.

#### 28. Which churn metric matters most?

It depends on business cost:

- If missing a churner is expensive, prioritize recall.
- If retention offers are expensive, prioritize precision.
- F1 balances both.
- ROC AUC evaluates ranking.

#### 29. How would you explain a churn prediction?

I would show the strongest contributing factors, such as high recency, falling order frequency, reduced spend, poor support experience, or low campaign engagement. SHAP could provide customer-level explanations.

#### 30. How does forecasting work?

Historical monthly revenue is converted into lag and rolling-window features. A boosting model predicts future months recursively, and validation error is used to create an approximate interval.

#### 31. Why not randomly split time-series data?

Random splitting allows future patterns to influence training for earlier periods and creates unrealistically optimistic results. Time-ordered validation reflects real forecasting.

#### 32. What could improve the forecast?

- More years of data
- Promotions and holidays
- Price changes
- Marketing spend
- External economic variables
- Hierarchical product/market forecasts
- Backtesting across multiple time windows

### API and software-engineering questions

#### 33. Why FastAPI?

FastAPI offers high performance, type validation, dependency injection, automatic OpenAPI documentation, and clean integration with Python analytical services.

#### 34. Why keep business logic outside API routes?

Thin routes are easier to test and maintain. The same analytics services can be called by APIs, scripts, tests, or scheduled jobs.

#### 35. How did you apply modular design?

The project separates:

- API routing
- Configuration
- Database models and sessions
- Pydantic schemas
- Ingestion services
- Customer 360 services
- Analytics services
- ML services
- Frontend presentation

#### 36. How did you handle errors?

Domain-specific exceptions represent validation or insufficient-data conditions. FastAPI translates them into appropriate HTTP responses, and the UI displays user-readable errors.

#### 37. What is idempotency?

Running the same operation multiple times produces the same result without duplicate side effects. File checksums provide idempotent ingestion.

#### 38. What design pattern is used?

The architecture uses service-layer and repository-like separation. Configuration is centralized, dependency injection provides database sessions, and ML pipelines combine preprocessing and estimators.

#### 39. How are model artifacts versioned?

Training stores the model binary under the artifacts directory and stores run ID, model type, model name, version, metrics, and artifact path in `model_runs`.

### Streamlit and deployment questions

#### 40. Why Streamlit?

It allowed a polished analytical interface to be built entirely in Python while supporting Plotly, data tables, uploads, caching, and rapid deployment.

#### 41. Why does the cloud app not use FastAPI?

Streamlit Community Cloud hosts the Streamlit process but does not automatically host a second FastAPI service. The cloud version therefore reads compact Parquet data directly. The local/Docker architecture still supports the API.

#### 42. Are uploaded cloud files persisted?

No. They are processed in the current session and removed when the session ends. Persistent uploads require external storage and a hosted backend/database.

#### 43. How would you add persistent cloud uploads?

I would deploy FastAPI separately, connect managed PostgreSQL and object storage, authenticate users, and send uploads from Streamlit to the API.

#### 44. How does deployment update?

Streamlit Community Cloud watches the GitHub `main` branch. A pushed commit triggers automatic redeployment.

#### 45. What deployment issues occurred?

- Entrypoint-relative module import failure
- Missing Scikit-learn and PyArrow in the frontend requirements
- Disabled cloud upload UX

Each issue was diagnosed from the traceback, fixed locally, tested, pushed, and automatically redeployed.

### Power BI and Excel questions

#### 46. How is Power BI connected?

The project generates normalized CSV exports from the governed analytical layer. Power BI imports these files and can calculate measures using the provided DAX definitions.

#### 47. How is Excel used?

Excel Power Query imports the same governed exports. Analysts can create PivotTables, charts, filters, and ad hoc analysis without recalculating source logic manually.

#### 48. Why not calculate every KPI separately in Power BI?

Core definitions should remain centralized. Power BI may calculate presentation measures, but customer features and governed business definitions should come from the shared analytical layer.

#### 49. What is a star schema for this project?

A future Power BI model could use:

- FactTransactions
- DimCustomer
- DimProduct
- DimDate
- DimGeography
- FactCampaign
- FactSupport

Customer 360 could remain a wide analytical table for customer-level reports.

#### 50. What Power BI visuals would you build?

- Executive KPI cards
- Revenue trend line
- Segment contribution donut
- Customer geography map
- CLV ranking
- Churn-risk distribution
- Cohort heatmap
- Recommendation action table

### Testing and DevOps questions

#### 51. What tests are included?

- Unit tests for cleaning and analytics
- Integration tests for APIs
- End-to-end customer journey tests
- Streamlit Cloud rendering test
- Cloud upload standardization test

#### 52. What does CI validate?

CI installs dependencies, runs Ruff, executes Pytest with coverage, validates Docker Compose, and builds backend and frontend images.

#### 53. Why Docker?

Docker provides reproducible environments and allows PostgreSQL, FastAPI, and Streamlit to run together with predictable dependencies.

#### 54. What would you monitor in production?

- API latency and error rate
- Ingestion failures
- Data freshness
- Missing-value and schema drift
- Model feature drift
- Prediction distribution
- Churn model precision and recall over time
- Forecast error
- Dashboard usage

#### 55. What security improvements are required?

- Authentication and role-based access
- Upload malware scanning
- File-size and content restrictions
- API rate limiting
- Managed secrets
- Encryption
- Audit logs
- Privacy and consent enforcement
- Row-level security

---

## 11. Questions about limitations

### What are the current limitations?

- The public deployment uses historical retail data.
- UCI data does not include real marketing or support events.
- Product cost is estimated to demonstrate profit.
- CLV is an interpretable approximation.
- The cloud upload is session-only.
- The deployed churn score is a behavioral risk score; the local backend supports model comparison.
- Streamlit Community Cloud is not a full multi-service production environment.

### How should limitations be discussed?

Do not hide them. Explain:

1. What the source data actually contains.
2. Which assumptions were necessary.
3. How assumptions are documented.
4. What would change in a real enterprise deployment.

This demonstrates analytical integrity.

---

## 12. Improvements for a production version

- Deploy FastAPI independently
- Use managed PostgreSQL
- Add object storage for raw uploads
- Add authentication and RBAC
- Add Alembic migrations
- Add Airflow or Dagster scheduling
- Add Great Expectations data-quality checks
- Add MLflow model registry
- Add SHAP explanations
- Add feature and prediction drift monitoring
- Add BG/NBD and Gamma-Gamma CLV
- Add recommendation evaluation and uplift modelling
- Add persistent user workspaces
- Add row-level security for Power BI
- Add automated Power BI refresh
- Add Kubernetes or managed container deployment

---

## 13. How to demonstrate the project in an interview

### Recommended demo sequence

1. Open Executive Summary.
2. Explain the source, transaction count, customer count, and date range.
3. Show revenue and segment composition.
4. Open Segmentation and explain RFM.
5. Open CLV and explain customer prioritization.
6. Open Churn Analytics and explain the 90-day definition.
7. Open Revenue Forecast and explain time-based validation.
8. Open Recommendations and show the action/reason/priority structure.
9. Open Data Management and upload the sample customer CSV.
10. Show validation, cleaning preview, and standardized download.
11. Briefly show the GitHub repository, tests, CI, Power BI exports, and architecture docs.

### What not to do

- Do not only click through charts.
- Do not claim missing fields existed in the source.
- Do not call the cloud version a complete enterprise production deployment.
- Do not focus only on model accuracy.
- Do not describe the dashboard before describing the business problem.

---

## 14. Resume bullets

- Built and deployed an end-to-end Customer360 intelligence platform using Python, FastAPI, SQLAlchemy, PostgreSQL, Scikit-learn, XGBoost, Plotly, Streamlit, Docker, and GitHub Actions.
- Engineered a governed customer analytical layer from 824K+ prepared transaction records covering 5.9K customers, 4.9K products, and 41 markets.
- Implemented RFM and K-Means segmentation, CLV, churn-risk analysis, revenue forecasting, KPI reporting, cohort analytics, and explainable next-best-action recommendations.
- Developed validated CSV/Excel ingestion with schema checks, type correction, duplicate handling, data-quality reporting, and idempotent file processing.
- Created Power BI and Excel-ready analytical exports and centralized KPI definitions to maintain consistency across reporting tools.
- Reduced large-data dashboard processing time from approximately 58 seconds to approximately 9 seconds through vectorized SQL loading and calculation reuse.
- Added automated unit, integration, end-to-end, Streamlit, and upload tests, with GitHub Actions validating code quality and Docker builds.

---

## 15. Behavioral interview answers

### Tell me about a difficult technical problem.

Use the large-data performance STAR story.

### Tell me about a time your first approach failed.

Use the Streamlit deployment or SQLite bulk-load story. Explain the evidence, root cause, correction, and verification.

### Tell me about a time you challenged a requirement.

Use the incomplete data-model story. Explain that the original schema could not support all requested metrics and that you redesigned it before writing misleading code.

### Tell me about a time you worked with ambiguity.

Explain how churn, CLV, customer health, cost, and cloud persistence required explicit definitions and documented assumptions.

### Tell me about a time you improved performance.

Explain the 58-second to 9-second improvement.

### Tell me about a time you ensured quality.

Discuss validation, automated tests, CI, Docker builds, data provenance, and avoiding fabricated source fields.

---

## 16. Short definitions to memorize

- **Customer 360:** A unified customer-level profile built from multiple operational sources.
- **RFM:** Recency, Frequency, and Monetary customer scoring.
- **CLV:** Expected economic value of a customer relationship.
- **Churn:** Loss or inactivity of a customer according to an explicit business definition.
- **ROC AUC:** Ability of a classifier to rank positive cases above negative cases.
- **MAE:** Average absolute forecasting error.
- **RMSE:** Error metric that penalizes large errors more strongly.
- **MAPE:** Average percentage forecasting error.
- **Idempotency:** Repeating an operation does not create duplicate effects.
- **Data leakage:** Training with information that would not be available at prediction time.
- **Feature engineering:** Transforming source data into model- or analysis-ready variables.
- **Data lineage:** Tracking where data and model outputs came from.
- **Star schema:** Fact tables connected to descriptive dimension tables.
- **CI/CD:** Automated validation and delivery of software changes.
- **Model drift:** Changes in data or behavior that reduce model reliability.

---

## 17. Final interview closing statement

> This project taught me that successful analytics is not just about training a model or building a dashboard. The difficult work is defining valid business metrics, designing the data model, creating reusable features, handling imperfect source data, validating assumptions, ensuring consistency across APIs and BI tools, and deploying a solution that users can actually operate. I can explain every assumption in this platform, the trade-offs I made, the issues I encountered, and how I would evolve it into a fully managed enterprise system.

