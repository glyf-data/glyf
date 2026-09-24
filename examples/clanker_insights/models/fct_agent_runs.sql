-- One row per agent run in the Acme Logistics workspace.
select
  run_id,
  cast(started_at as timestamp) as started_at,
  cast(started_at as date) as run_date,
  strftime(cast(started_at as date), '%G-W%V') as week,
  strftime(cast(started_at as timestamp), '%a') as weekday,
  isodow(cast(started_at as date)) as weekday_number,
  hour(cast(started_at as timestamp)) as hour,
  agent,
  model,
  trigger,
  outcome,
  nullif(error, '') as error,
  duration_s,
  tool_calls,
  input_tokens,
  output_tokens,
  input_tokens + output_tokens as tokens,
  cost_usd
from {{ source('raw', 'agent_runs') }}
