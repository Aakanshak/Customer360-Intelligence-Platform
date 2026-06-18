# Dataset provenance

## UCI Online Retail II

The portfolio dataset is **Online Retail II**, created by Daqing Chen and distributed by the UCI Machine Learning Repository.

- Repository: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- DOI: https://doi.org/10.24432/C5CG6D
- License: Creative Commons Attribution 4.0 International
- Original rows: 1,067,371
- Original period: December 1, 2009–December 9, 2011
- Original fields: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country

The preparation script filters records without customer identifiers from customer-level analytics, preserves cancellations, maps product codes to internal integer IDs, and creates transparent derived fields required by the platform.

No real names, emails, ages, genders, marketing events, or support cases are fabricated from this dataset. Fields absent from the source remain unknown or empty.
