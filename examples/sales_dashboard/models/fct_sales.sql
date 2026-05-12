select
  month,
  region,
  channel,
  sum(revenue) as revenue,
  sum(orders) as orders
from {{ source('raw', 'sales') }}
group by 1, 2, 3
