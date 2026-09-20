select
  weekday,
  weekday_number,
  hour,
  sum(sessions) as sessions
from {{ source('raw', 'hourly_activity') }}
group by 1, 2, 3
