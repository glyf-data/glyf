SELECT
  month,
  department,
  round(gross_margin * 100.0 / nullif(bookings, 0), 1) as margin_rate
FROM "finance_metrics"."main"."fct_finance"
ORDER BY month, department
