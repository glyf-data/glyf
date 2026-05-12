select
  week,
  plan,
  sum(active_users) as active_users,
  sum(activated_users) as activated_users,
  sum(sessions) as sessions
from {{ source('raw', 'product_usage') }}
group by 1, 2
