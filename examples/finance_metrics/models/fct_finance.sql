select
  month,
  department,
  sum(bookings) as bookings,
  sum(expenses) as expenses,
  sum(bookings - expenses) as gross_margin
from {{ source('raw', 'finance') }}
where department != 'Partners'
group by 1, 2
