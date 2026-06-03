# Dashboard Macros

Dashboard macros let YAML call Python functions that resolve into typed Glyf
components before HTML is rendered.

## Where macros work

Macros are allowed in two places today:

- `summary[]`
- `sections[].items[].component`

They must be full Jinja expressions such as:

```yaml
component: "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
```

Important rendering behavior:

- `summary[]` renders inside the **AI Summary** drawer, not the main dashboard body
- `sections[].items[].component` renders directly in the dashboard grid

Example:

```yaml
summary:
  - "{{ product_owner() }}"
  - "{{ label_value('Generated', now('%Y-%m-%d %H:%M')) }}"

sections:
  - title: Status
    items:
      - component: "{{ alert.info('Refresh complete', 'Notification') }}"
      - component: "{{ ui.link('Open glyfdata.com', 'https://glyfdata.com') }}"
```

The `examples/product_analytics/dashboards/macro_showcase.yml` dashboard exists
as a demo project for these patterns. Its summary macros also appear in a
visible section so you can compare drawer output with in-page component output.

## UI Macros

UI macros return general-purpose dashboard components.

| Macro | Returns |
| --- | --- |
| `ui.label_value(label, value, note=None, width=None)` | Compact key/value block |
| `ui.text(value, title=None, width=None)` | Text block |
| `ui.list(values, title=None, width=None)` | List component |
| `ui.listofvalues(values, title=None, width=None)` | Alias of `ui.list(...)` |
| `ui.badge(label, tone='neutral', width=None)` | Badge |
| `ui.link(label, href, title=None, width=None)` | Link block |

Recommended usage:

- prefer `ui.list(...)` as the canonical list helper
- use `ui.listofvalues(...)` only when keeping older examples or matching existing copy

There is no runtime difference between `ui.list` and `listofvalues` today.
Both resolve to the same underlying list component.

Example:

```yaml
sections:
  - title: UI Macros
    items:
      - component: "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
      - component: "{{ ui.text('Pipeline-owned dashboards.', title='Context') }}"
      - component: "{{ ui.list(['Revenue', 'Activation', 'Retention'], title='Metrics') }}"
      - component: "{{ ui.badge('Ready', tone='success') }}"
      - component: "{{ ui.link('Open docs', 'https://glyfdata.com', title='Project') }}"
```

## Alert Macros

Alert macros render status-oriented callouts.

| Macro | Returns |
| --- | --- |
| `alert.message(value, title=None, tone='info', width=None)` | Generic alert |
| `alert.info(value, title=None, width=None)` | Informational alert |
| `alert.success(value, title=None, width=None)` | Success alert |
| `alert.warning(value, title=None, width=None)` | Warning alert |
| `alert.error(value, title=None, width=None)` | Error alert |
| `echo(value, title=None)` | Alias of `alert.info(...)` |

Example:

```yaml
sections:
  - title: Alerts
    items:
      - component: "{{ alert.message('Generic message', title='alert.message', tone='info') }}"
      - component: "{{ alert.success('Everything is healthy.', 'Health') }}"
      - component: "{{ alert.warning('Threshold exceeded.', 'Freshness') }}"
      - component: "{{ alert.error('Missing source data.', 'Incident') }}"
```

## AI Insights

The `summary[]` field renders into the dashboard AI Summary drawer. These macros
are best for precomputed commentary, signals, and contextual notes.

| Macro | Returns |
| --- | --- |
| `ai.summary(value, title='Overview', width=None)` | Summary text block |
| `ai.insight(value, title=None, tone='info', width=None)` | Signal-style alert |
| `ai.signal(value, title=None, tone='info', width=None)` | Alias of `ai.insight(...)` |

Example:

```yaml
summary:
  - "{{ ai.summary('Revenue moved up this month.') }}"
  - "{{ ai.insight('Starter churn needs review.', tone='warning') }}"
  - "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
```

If you want the same content visible in the page body, repeat it as a
`component:` item in a section.

## Helpers And Time

These helpers are lightweight aliases and string-returning utilities used inside
other dashboard macros.

### Time

| Macro | Returns |
| --- | --- |
| `time.now(format='%Y-%m-%d %H:%M', timezone=None)` | Formatted timestamp string |
| `now(format='%Y-%m-%d %H:%M', timezone=None)` | Alias of `time.now(...)` |

Example:

```yaml
summary:
  - "{{ label_value('Generated', now('%Y-%m-%d %H:%M')) }}"
```

### Convenience aliases

These map directly to existing built-ins:

- `label_value(...)`
- `text(...)`
- `link(...)`
- `badge(...)`
- `listofvalues(...)`
- `echo(...)`

They exist for terser YAML, but namespace-prefixed calls like `ui.label_value`
or `alert.info` are usually clearer in larger dashboards.

## Custom Macros

Project-local dashboard macros live in:

```text
dashboards/macros.py
```

They can return any valid Glyf `ComponentSpec`.

Example:

```python
from glyf.dashboard import components as c


def product_owner():
    return c.label_value("Owner", "Product Analytics")


def activation_health(rate: float):
    if rate >= 0.8:
        return c.alert("Activation is tracking above target.", title="Health", tone="success")
    return c.alert("Activation needs attention.", title="Health", tone="warning")
```

Used in YAML:

```yaml
summary:
  - "{{ product_owner() }}"

sections:
  - title: Activation
    items:
      - component: "{{ activation_health(0.67) }}"
```

## Current Boundary

Custom macros evaluate against the YAML expression context. They do **not**
receive GGSQL result rows or chart data automatically.

That means a call like:

```yaml
- component: "{{ activation_health(0.67) }}"
```

uses the literal value `0.67` because that is what YAML passed into the macro.

Today, macros can evaluate:

- hardcoded arguments
- strings returned by helpers like `time.now(...)`
- other project macro calls

They cannot yet directly consume:

- a chart's aggregated result value
- GGSQL query output
- another dashboard component's rendered state

If Glyf grows artifact-aware macros later, that would likely be a separate
feature where macros can read named chart metadata or derived metric values from
generated artifacts rather than raw GGSQL execution directly.
