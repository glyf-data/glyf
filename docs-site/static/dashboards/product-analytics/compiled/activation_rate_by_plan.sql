SELECT
  week,
  plan,
  round(sum(activated_users) * 100.0 / nullif(sum(active_users), 0), 1) as activation_rate
FROM "product_analytics"."main"."fct_product_usage"
GROUP BY 1, 2
