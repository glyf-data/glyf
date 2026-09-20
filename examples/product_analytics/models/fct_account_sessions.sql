select
  account_id,
  plan,
  sessions,
  avg_session_minutes
from {{ source('raw', 'account_sessions') }}
