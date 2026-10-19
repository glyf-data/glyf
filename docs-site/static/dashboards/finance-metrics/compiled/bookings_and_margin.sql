SELECT
  month,
  sum(bookings) as bookings,
  round(sum(gross_margin) * 100.0 / nullif(sum(bookings), 0), 1) as margin_rate
FROM "finance_metrics"."main"."fct_finance"
GROUP BY 1
ORDER BY 1, bookings, margin_rate
