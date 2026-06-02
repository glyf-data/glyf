SELECT week, sum(active_users) as active_users
FROM "product_analytics"."main"."fct_product_usage"
GROUP BY 1
