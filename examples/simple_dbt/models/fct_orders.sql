select
  month,
  sum(revenue) as revenue
from {{ source('raw', 'orders') }}
group by 1
