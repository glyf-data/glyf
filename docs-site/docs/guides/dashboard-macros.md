# Dashboard Macros

Dashboard macros let YAML call Python functions that resolve into typed Glyf
components before HTML is rendered.

## Where macros work

Macros are allowed in two places:

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

`examples/product_analytics/dashboards/macro_showcase.yml` demonstrates every
macro on this page; its summary macros are repeated in a visible section so
drawer output and in-page output can be compared side by side.

## UI Macros

UI macros return general-purpose dashboard components.

| Macro | Returns |
| --- | --- |
| `ui.label_value(label, value, note=None, width=None)` | Compact key/value block |
| `ui.text(value, title=None, note=None, width=None)` | Text block |
| `ui.list(values, title=None, note=None, width=None)` | List component |
| `ui.listofvalues(values, title=None, note=None, width=None)` | Alias of `ui.list(...)` |
| `ui.badge(label, tone='neutral', width=None)` | Badge |
| `ui.link(label, href, title=None, width=None)` | Link block |

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
| `alert.message(value, title=None, tone='info', metric=None, note=None, trigger=None, width=None)` | Generic alert |
| `alert.info(value, title=None, metric=None, note=None, trigger=None, width=None)` | Informational alert |
| `alert.success(value, title=None, metric=None, note=None, trigger=None, width=None)` | Success alert |
| `alert.warning(value, title=None, metric=None, note=None, trigger=None, width=None)` | Warning alert |
| `alert.error(value, title=None, metric=None, note=None, trigger=None, width=None)` | Error alert |
| `alert.threshold(chart, field, value, op='lt', title=None, ...)` | Artifact-aware threshold alert |
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
      - component: "{{ alert.threshold('active_users', 'active_users', 4200, op='lt', title='Active users threshold') }}"
```

An alert given a `metric` becomes a status card: the number large, in the
alert's tone, the message under it, and the card edged in the same colour.
`note` adds a footnote under a dashed rule, on alerts, text and lists alike;
use it to say where a number came from.

`trigger` marks an alert that the data raised when glyf built the page, rather
than one written by hand. The card gets an **Auto-triggered** pill with a
lightning icon, and hovering it shows the rule, such as
`latest-week average 28.5% < 40% target`. `alert.threshold(...)` sets it for
you; a custom macro that picks a tone from a value should pass it too.

```yaml
sections:
  - title: Health
    items:
      - component: "{{ alert.warning('Below its 40% target.', 'Activation health', metric='37.4%', note='Average of the plans in the latest week.') }}"
      - component: "{{ ui.list(['Activated means onboarding finished that week.', 'The 40% target is for this quarter.'], title='Reading activation') }}"
```

`alert.threshold(...)` reads the latest value from the named chart artifact and
compares it to the provided threshold. It works best with single-series charts
or with custom macros that know how to derive a grouped value.

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

### Artifact helpers

These helpers read from the normalized `.data.json` chart artifacts generated by
`glyf render`:

| Helper | Returns |
| --- | --- |
| `source(chart, field)` | Distinct values from a chart field |
| `distinct_values(chart, field)` | Same as `source(...)` |
| `latest_value(chart, field)` | Last non-null value for a field |

Example:

```yaml
sections:
  - title: Artifact helpers
    items:
      - component: "{{ ui.list(source('activation_by_plan', 'plan'), title='Plans') }}"
      - component: "{{ ui.label_value('Latest active users', latest_value('active_users', 'active_users')) }}"
```

## Custom Macros

Project-local dashboard macros live in:

```text
dashboards/macros.py
```

They can return any valid Glyf `ComponentSpec`.

Example:

```python
from glyf.dashboard import components as c
from glyf.dashboard.macros import MacroContext


def product_owner() -> c.ComponentSpec:
    return c.label_value("Owner", "Growth team")


def product_notes() -> c.ComponentSpec:
    # Notes a reader needs beside the activation charts. Nothing here is
    # queried: a macro returns fixed text as readily as a number.
    return c.values_list(
        [
            "Activated means the user finished onboarding in that week.",
            "The 40% target is the Growth team's for this quarter.",
        ],
        title="Reading activation",
    )


def activation_health(
    ctx: MacroContext,
    *,
    chart: str = "activation_rate_by_plan",
    field: str = "activation_rate",
    threshold: float = 80.0,
) -> c.ComponentSpec:
    latest_rate = float(ctx.latest_value(chart, field))
    tone = "success" if latest_rate >= threshold else "warning"
    message = "On track." if tone == "success" else f"Below its {threshold:g}% target."
    return c.alert(
        message,
        title="Activation health",
        tone=tone,
        metric=f"{latest_rate:.1f}%",
        trigger=f"latest rate {latest_rate:.1f}% against a {threshold:g}% target",
    )
```

Used in YAML:

```yaml
summary:
  - "{{ product_owner() }}"

sections:
  - title: Activation
    items:
      - component: "{{ activation_health(chart='activation_rate_by_plan', field='activation_rate', threshold=40) }}"
      - component: "{{ product_notes() }}"
```

If the first argument is named `ctx`, Glyf injects a `MacroContext` during
dashboard rendering. That context can read normalized chart artifact data:

- `ctx.chart_fields(chart)`
- `ctx.chart_rows(chart)`
- `ctx.chart_values(chart, field)`
- `ctx.distinct_values(chart, field)`
- `ctx.latest_value(chart, field)`

Simple macros without `ctx` still work exactly as before. Use `ctx` only when
the macro needs real chart values instead of hardcoded YAML arguments.
