select
  month,
  region,
  sum(revenue) as revenue
from {{ source('raw', 'orders') }}
group by 1, 2
