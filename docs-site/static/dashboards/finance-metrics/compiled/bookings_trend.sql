SELECT month, sum(bookings) as bookings
FROM "finance_metrics"."main"."fct_finance"
GROUP BY 1
