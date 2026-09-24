-- One row per ISO week: the numbers the headline tiles compare.
select
  week,
  count(*) as runs,
  count(*) filter (where outcome = 'succeeded') as succeeded,
  round(100.0 * count(*) filter (where outcome = 'succeeded') / count(*), 1) as success_rate,
  round(sum(cost_usd), 2) as spend_usd,
  round(median(duration_s), 1) as median_duration_s
from {{ ref('fct_agent_runs') }}
group by 1
