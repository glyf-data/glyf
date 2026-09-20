select
  invoice_id,
  month,
  segment,
  amount,
  discount_pct,
  days_to_pay
from {{ source('raw', 'invoices') }}
