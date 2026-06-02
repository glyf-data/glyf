SELECT month, channel, sum(revenue) as revenue
FROM "sales_dashboard"."main"."fct_sales"
GROUP BY 1, 2
