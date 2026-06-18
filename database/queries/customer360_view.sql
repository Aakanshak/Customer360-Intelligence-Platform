CREATE OR REPLACE VIEW customer360_master AS
SELECT
    c.customer_id,
    c.name,
    c.age,
    c.gender,
    c.city,
    c.state,
    c.signup_date,
    COUNT(DISTINCT t.transaction_id) AS order_count,
    COALESCE(SUM(t.order_amount), 0) AS total_revenue,
    COALESCE(SUM(t.order_amount - t.cost_amount - t.discount_amount), 0) AS total_profit,
    COALESCE(AVG(t.order_amount), 0) AS average_order_value,
    MAX(t.order_date) AS last_purchase_date,
    COUNT(DISTINCT t.product_id) AS product_diversity,
    COUNT(DISTINCT m.campaign_id) AS campaigns_received,
    COALESCE(AVG(CASE WHEN m.campaign_response THEN 1.0 ELSE 0.0 END), 0) AS campaign_response_rate,
    COUNT(DISTINCT s.ticket_id) AS support_ticket_count,
    COALESCE(AVG(s.resolution_time), 0) AS avg_resolution_hours
FROM customers c
LEFT JOIN transactions t ON t.customer_id = c.customer_id AND t.status = 'completed'
LEFT JOIN marketing_activities m ON m.customer_id = c.customer_id
LEFT JOIN support_tickets s ON s.customer_id = c.customer_id
GROUP BY c.customer_id, c.name, c.age, c.gender, c.city, c.state, c.signup_date;
