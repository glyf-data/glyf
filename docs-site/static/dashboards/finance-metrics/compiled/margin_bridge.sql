SELECT 0 AS step_order, 'Bookings' AS step, sum(bookings) AS amount
FROM "finance_metrics"."main"."fct_finance"
UNION ALL
SELECT 1, department || ' expenses', -sum(expenses)
FROM "finance_metrics"."main"."fct_finance"
GROUP BY department
ORDER BY step_order, amount
