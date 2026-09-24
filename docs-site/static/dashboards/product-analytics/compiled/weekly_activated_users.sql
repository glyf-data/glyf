WITH weekly AS (
  SELECT week, sum(activated_users) AS activated_users
  FROM "product_analytics"."main"."fct_product_usage"
  GROUP BY 1
)
SELECT activated_users, lag(activated_users) OVER (ORDER BY week) AS previous
FROM weekly
ORDER BY week DESC
LIMIT 1
