SELECT city, format, revenue
FROM "sales_dashboard"."main"."raw_stores"
ORDER BY revenue DESC, city, format
