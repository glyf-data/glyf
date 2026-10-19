SELECT week, plan, sum(sessions) as sessions
FROM "product_analytics"."main"."fct_product_usage"
GROUP BY 1, 2
ORDER BY 1, 2, sessions
