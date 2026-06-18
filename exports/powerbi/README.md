# Power BI data mart

These governed CSV exports are generated from the same Customer360 analytical layer used by Streamlit.

Recommended Power BI model:

- `customer360.csv`: customer dimension and behavioral measures
- `products.csv`: product dimension
- `monthly_revenue.csv`: monthly trend aggregate
- `segments.csv`: segment summary
- `geography.csv`: market summary
- `category_revenue.csv`: product-category summary
- `recommendations.csv`: next-best-action worklist

Refresh the files with:

```bash
python scripts/build_bi_exports.py
```

For Power BI Desktop, use **Get Data → Text/CSV** and load the required files. Build executive KPI cards from `customer360.csv`, trend visuals from `monthly_revenue.csv`, and action tables from `recommendations.csv`.
