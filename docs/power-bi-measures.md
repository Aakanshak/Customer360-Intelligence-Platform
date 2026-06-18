# Suggested Power BI DAX measures

```dax
Total Revenue = SUM(customer360[total_revenue])

Total Profit = SUM(customer360[total_profit])

Customer Count = DISTINCTCOUNT(customer360[customer_id])

Average Order Value =
DIVIDE(
    SUM(customer360[total_revenue]),
    SUM(customer360[order_count])
)

At Risk Customers =
CALCULATE(
    DISTINCTCOUNT(customer360[customer_id]),
    customer360[recency_days] > 90
)

Retention Rate =
1 - DIVIDE([At Risk Customers], [Customer Count])

Predicted CLV = SUM(customer360[predicted_clv])
```

Recommended report pages:

1. Executive Overview
2. Customer Segmentation
3. CLV and Retention
4. Geographic Performance
5. Product and Category Performance
6. Next Best Actions
