WITH weekly AS (
  SELECT week, sum(sessions) AS sessions
  FROM "product_analytics"."main"."fct_product_usage"
  GROUP BY 1
)
SELECT sessions, lag(sessions) OVER (ORDER BY week) AS previous
FROM weekly
ORDER BY week DESC
LIMIT 1
