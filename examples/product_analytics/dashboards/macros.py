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
            "The rate is activated over active users within each plan, "
            "so Team, the smallest at about 330 users, swings the most.",
            "The 40% target is the Growth team's for this quarter, "
            "checked against the average of the three plans' rates.",
            "Free users who upgrade mid-week count toward the plan they end the week on.",
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
    latest_average = _latest_week_average(ctx, chart, field)
    on_track = latest_average >= threshold
    trigger = (
        f"latest-week average {latest_average:.1f}% "
        f"{'>=' if on_track else '<'} {threshold:g}% target"
    )
    if on_track:
        return c.alert(
            f"Activation is on track, above its {threshold:g}% target.",
            title="Activation health",
            tone="success",
            metric=f"{latest_average:.1f}%",
            trigger=trigger,
        )
    return c.alert(
        f"Activation needs attention: below its {threshold:g}% target.",
        title="Activation health",
        tone="warning",
        metric=f"{latest_average:.1f}%",
        trigger=trigger,
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
