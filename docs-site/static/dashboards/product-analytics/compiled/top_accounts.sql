SELECT account_id, plan, sessions, avg_session_minutes
FROM "product_analytics"."main"."fct_account_sessions"
ORDER BY sessions DESC, account_id, plan, avg_session_minutes
LIMIT 10
