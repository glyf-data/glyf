from glyf.dashboard import components as c
from glyf.dashboard.macros import MacroContext


def product_owner() -> c.ComponentSpec:
    return c.label_value("Owner", "Product Analytics")


def activation_health(
    ctx: MacroContext,
    *,
    chart: str = "activation_rate_by_plan",
    field: str = "activation_rate",
    threshold: float = 80.0,
) -> c.ComponentSpec:
    latest_average = _latest_week_average(ctx, chart, field)
    if latest_average >= threshold:
        return c.alert(
            f"Activation is tracking above target at {latest_average:.1f}%.",
            title="Health",
            tone="success",
        )
    return c.alert(
        f"Activation needs attention at {latest_average:.1f}%.",
        title="Health",
        tone="warning",
    )


def status_emoji(
    ctx: MacroContext,
    *,
    chart: str = "activation_rate_by_plan",
    field: str = "activation_rate",
    threshold: float = 80.0,
) -> str:
    latest_average = _latest_week_average(ctx, chart, field)
    if latest_average >= threshold:
        return "🟢 On track"
    return "🟠 Needs review"


def _latest_week_average(ctx: MacroContext, chart: str, field: str) -> float:
    rows = ctx.chart_rows(chart)
    if not rows:
        raise ValueError(f"chart '{chart}' does not contain any rows")

    week_field = "week" if "week" in ctx.chart_fields(chart) else None
    if week_field is None:
        values = [float(value) for value in ctx.chart_values(chart, field)]
        return sum(values) / len(values)

    latest_week = max(str(row[week_field]) for row in rows if row.get(week_field) is not None)
    values = [
        float(row[field])
        for row in rows
        if row.get(week_field) is not None
        and str(row[week_field]) == latest_week
        and row.get(field) is not None
    ]
    if not values:
        raise ValueError(f"chart '{chart}' field '{field}' does not contain any values")
    return sum(values) / len(values)
