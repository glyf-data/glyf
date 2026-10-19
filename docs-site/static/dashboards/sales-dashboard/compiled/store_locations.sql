SELECT city, latitude, longitude, revenue, format
FROM "sales_dashboard"."main"."raw_stores"
ORDER BY revenue DESC, city, latitude, longitude, format
