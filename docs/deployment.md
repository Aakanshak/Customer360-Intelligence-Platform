# Deployment guide

## Streamlit Community Cloud

The deployed app is self-contained and reads the committed Parquet data mart. A separate FastAPI service is not required.

1. Push the repository to GitHub.
2. Open https://share.streamlit.io/
3. Select **Create app**.
4. Choose the GitHub repository and `main` branch.
5. Set the main file path to `frontend/app.py`.
6. Deploy.

Streamlit installs dependencies from the root `requirements.txt`.

## Local application

The local application supports two modes:

- Bundled mode: run `streamlit run frontend/app.py`.
- API mode: set `API_URL=http://localhost:8000`, start FastAPI, then start Streamlit.

## Power BI

Run `python scripts/build_bi_exports.py`, then load files from `exports/powerbi/` through Power BI Desktop's Text/CSV connector.

## Excel

The same files can be imported through Excel Power Query using **Data → Get Data → From Text/CSV**. Use `customer360.csv` as the primary analytical table and the smaller aggregate files for charts and pivots.
