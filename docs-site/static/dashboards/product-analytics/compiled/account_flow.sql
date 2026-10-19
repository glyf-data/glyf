WITH accounts AS (
  SELECT
    plan,
    CASE
      WHEN sessions >= 40 THEN 'Heavy use'
      WHEN sessions >= 15 THEN 'Regular use'
      ELSE 'Light use'
    END AS activity,
    CASE WHEN avg_session_minutes >= 15 THEN 'Long sessions' ELSE 'Short sessions' END AS session_length
  FROM "product_analytics"."main"."fct_account_sessions"
)
SELECT plan AS stage, activity AS next_stage, count(*) AS accounts
FROM accounts
GROUP BY 1, 2
UNION ALL
SELECT activity, session_length, count(*)
FROM accounts
GROUP BY 1, 2
ORDER BY 1, 2
