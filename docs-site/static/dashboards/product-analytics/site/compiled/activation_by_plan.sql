SELECT week, plan, sum(activated_users) as activated_users
FROM "product_analytics"."main"."fct_product_usage"
GROUP BY 1, 2
