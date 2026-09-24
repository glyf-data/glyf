SELECT month, department, sum(expenses) as expenses
FROM "finance_metrics"."main"."fct_finance"
GROUP BY 1, 2
ORDER BY month, department, expenses
