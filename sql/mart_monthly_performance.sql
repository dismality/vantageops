-- Executive revenue and margin model used by the dashboard.
SELECT
  DATE(order_date, 'start of month') AS month,
  SUM(units * unit_price * (1 - discount_pct)) AS net_revenue,
  SUM(units * unit_price * (1 - discount_pct) - units * unit_cost - freight_cost) AS gross_profit,
  COUNT(DISTINCT order_id) AS orders,
  SUM(units) AS units
FROM fact_sales
GROUP BY DATE(order_date, 'start of month')
ORDER BY month;
