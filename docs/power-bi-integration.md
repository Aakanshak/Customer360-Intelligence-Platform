# Power BI integration

Use **Get Data → Web** and connect to:

`http://localhost:8000/api/v1/exports/customer360.csv`

For production, replace localhost with the deployed API host and configure scheduled refresh through the Power BI gateway. The export includes customer-level RFM and behavioral features. Executive aggregates are also available as JSON from `/api/v1/dashboard`.
