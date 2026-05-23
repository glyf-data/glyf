SELECT
  month,
  sum(gross_margin) as gross_margin
FROM "finance_metrics"."main"."fct_finance"
GROUP BY 1
