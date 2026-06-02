SELECT
  week,
  round(sum(sessions) * 1.0 / nullif(sum(active_users), 0), 2) as sessions_per_user
FROM "product_analytics"."main"."fct_product_usage"
GROUP BY 1
