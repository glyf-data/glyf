SELECT 1 AS step_order, 'All accounts' AS step, count(*) AS accounts
FROM "product_analytics"."main"."fct_account_sessions"
UNION ALL
SELECT 2, 'Regular use', count(*)
FROM "product_analytics"."main"."fct_account_sessions"
WHERE sessions >= 15
UNION ALL
SELECT 3, 'Heavy use', count(*)
FROM "product_analytics"."main"."fct_account_sessions"
WHERE sessions >= 40
UNION ALL
SELECT 4, 'Heavy use, long sessions', count(*)
FROM "product_analytics"."main"."fct_account_sessions"
WHERE sessions >= 40 AND avg_session_minutes >= 15
ORDER BY step_order
