WITH weekly AS (
  SELECT week, sum(active_users) AS active_users
  FROM "product_analytics"."main"."fct_product_usage"
  GROUP BY 1
)
SELECT active_users, lag(active_users) OVER (ORDER BY week) AS previous
FROM weekly
ORDER BY week DESC
LIMIT 1
