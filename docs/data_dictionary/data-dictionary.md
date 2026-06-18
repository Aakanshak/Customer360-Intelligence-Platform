# Data dictionary

| Entity | Grain | Key fields | Purpose |
|---|---|---|---|
| customers | One customer | customer_id, signup_date, state | Identity and demographics |
| products | One product | product_id, category, price, cost | Product and margin analysis |
| transactions | One order line | transaction_id, customer_id, product_id, order_date | Revenue, profit, RFM and forecasting |
| marketing_activities | One customer campaign touch | campaign_id, customer_id, response | Conversion and campaign effectiveness |
| support_tickets | One support case | ticket_id, customer_id, resolution time | Service experience and churn features |
| ingestion_batches | One uploaded file | batch_id, checksum | Auditability and idempotency |
| model_runs | One model training run | run_id, model type, metrics | Model lineage and versioning |

Monetary values are non-negative. Customer age is constrained to 16–110. All analytical dates use the application server's UTC clock.

## UCI mapping

For the included Online Retail II data:

- `Customer ID` becomes `customer_id`.
- `StockCode` is mapped deterministically to an integer `product_id`.
- `Description` becomes `product_name` and is categorized using transparent keyword rules.
- `Quantity × Price` becomes `order_amount`.
- Cancellation invoices and negative quantities are retained with `status = cancelled`.
- Country is represented in the geographic `state` field.
- Customer names are anonymized labels because the source contains no personal names.
- Cost is estimated at 65% of sales solely to enable a demonstrative margin KPI; it is not an observed source field.
