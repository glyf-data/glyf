SELECT
  weekday,
  hour,
  sessions
FROM "product_analytics"."main"."fct_hourly_activity"
ORDER BY weekday_number, hour, weekday, sessions
