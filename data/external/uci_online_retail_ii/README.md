# UCI Online Retail II

- Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- DOI: https://doi.org/10.24432/C5CG6D
- Creator: Daqing Chen
- License: Creative Commons Attribution 4.0 International
- Coverage: December 1, 2009 through December 9, 2011
- Size: 1,067,371 transaction rows in the original workbook

The original ZIP and workbook are retained in this directory. Run:

```bash
python scripts/prepare_uci_retail.py
```

to regenerate analysis-ready Parquet tables under `data/processed/uci_online_retail_ii`.
