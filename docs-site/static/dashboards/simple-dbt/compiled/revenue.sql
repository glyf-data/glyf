SELECT month, sum(revenue) AS revenue
FROM "simple_dbt"."main"."fct_orders"
GROUP BY 1
ORDER BY 1, revenue
