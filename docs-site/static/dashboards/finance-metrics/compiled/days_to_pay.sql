SELECT
  days_to_pay,
  segment
FROM "finance_metrics"."main"."fct_invoices"
ORDER BY days_to_pay, segment
