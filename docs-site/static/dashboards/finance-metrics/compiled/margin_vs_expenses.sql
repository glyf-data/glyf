SELECT
  department,
  expenses,
  gross_margin
FROM "finance_metrics"."main"."fct_finance"
ORDER BY department, expenses
