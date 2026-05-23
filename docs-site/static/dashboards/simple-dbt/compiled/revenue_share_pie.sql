SELECT region, sum(revenue) as revenue
FROM "simple_dbt"."main"."fct_orders"
GROUP BY 1
