"""Regenerate the seed CSVs of the finance_metrics, product_analytics and
clanker_insights examples.

The data is synthetic. The generator is seeded, so running it again writes the
same files byte for byte; change `SEED` or the shapes below and commit the
result to change the examples.

    uv run python examples/seed_data.py
"""

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 29
EXAMPLES = Path(__file__).parent

WEEKS = [f"2026-W{week:02d}" for week in range(1, 13)]
MONTHS = [f"2025-{month:02d}" for month in range(4, 13)] + [
    f"2026-{month:02d}" for month in range(1, 4)
]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# plan: (active users in week 1, weekly growth, activation rate, sessions per user)
PLANS = {
    "Free": (900, 0.035, 0.14, 2.8),
    "Pro": (420, 0.050, 0.43, 4.6),
    "Team": (160, 0.065, 0.58, 6.9),
}

# plan: (accounts, median sessions per account, median session minutes)
ACCOUNTS = {
    "Free": (120, 9, 6.0),
    "Pro": (80, 24, 13.5),
    "Team": (40, 61, 21.0),
}

# department: (bookings in month 1, monthly growth, expense ratio)
DEPARTMENTS = {
    "Sales": (38000, 0.030, 0.36),
    "Product": (16000, 0.045, 1.10),
    "Services": (11000, 0.020, 0.72),
    "Partners": (6000, 0.060, 0.55),
}

# segment: (invoices, median amount, median days to pay, typical discount %)
SEGMENTS = {
    "SMB": (150, 1800, 18, 4.0),
    "Mid-market": (100, 9500, 31, 11.0),
    "Enterprise": (50, 42000, 47, 21.0),
}


# Clanker is an AI agent platform; its insights page shows one customer
# workspace, Acme Logistics, what its agents did over six weeks. Its own seed,
# so changing it leaves the other examples' files as they are.
CLANKER_SEED = 42
CLANKER_START = date(2026, 8, 10)
CLANKER_DAYS = 42
# agent: (runs a day at the start, weekly growth, success rate, escalation
# rate, median seconds, tool calls per run, models with their share)
CLANKER_AGENTS = {
    "Support Triage": (22, 0.06, 0.93, 0.04, 14, 3, {"clank-mini": 0.8, "clank-pro": 0.2}),
    "Invoice Parser": (14, 0.03, 0.96, 0.01, 21, 2, {"clank-mini": 1.0}),
    "Code Reviewer": (8, 0.09, 0.84, 0.06, 95, 7, {"clank-pro": 0.6, "clank-ultra": 0.4}),
    "Lead Enricher": (10, 0.02, 0.89, 0.02, 33, 5, {"clank-mini": 0.5, "clank-pro": 0.5}),
    "On-call Summarizer": (4, 0.04, 0.9, 0.08, 62, 9, {"clank-ultra": 1.0}),
}
# model: (dollars per thousand input tokens, per thousand output tokens)
CLANKER_MODELS = {
    "clank-mini": (0.004, 0.016),
    "clank-pro": (0.03, 0.12),
    "clank-ultra": (0.12, 0.48),
}
# What the platform charges for each run, on top of the model's tokens.
CLANKER_RUN_FEE = 0.02
CLANKER_TRIGGERS = {"API": 0.45, "Schedule": 0.25, "Slack": 0.2, "Webhook": 0.1}
CLANKER_ERRORS = {
    "Tool timeout": 0.38,
    "Rate limited": 0.22,
    "Invalid output": 0.25,
    "Auth expired": 0.15,
}


def main(examples: Path = EXAMPLES) -> None:
    rng = random.Random(SEED)
    product = examples / "product_analytics" / "seeds"
    finance = examples / "finance_metrics" / "seeds"

    _write(
        product / "raw_product_usage.csv",
        ["week", "plan", "active_users", "activated_users", "sessions"],
        _product_usage(rng),
    )
    _write(
        product / "raw_account_sessions.csv",
        ["account_id", "plan", "sessions", "avg_session_minutes"],
        _account_sessions(rng),
    )
    _write(
        product / "raw_hourly_activity.csv",
        ["weekday", "weekday_number", "hour", "sessions"],
        _hourly_activity(rng),
    )
    _write(
        finance / "raw_finance.csv",
        ["month", "department", "bookings", "expenses"],
        _finance(rng),
    )
    _write(
        finance / "raw_invoices.csv",
        ["invoice_id", "month", "segment", "amount", "discount_pct", "days_to_pay"],
        _invoices(rng),
    )
    _write(
        examples / "clanker_insights" / "seeds" / "raw_agent_runs.csv",
        [
            "run_id", "started_at", "agent", "model", "trigger", "outcome",
            "error", "duration_s", "tool_calls", "input_tokens", "output_tokens",
            "cost_usd",
        ],
        _agent_runs(random.Random(CLANKER_SEED)),
    )


def _product_usage(rng: random.Random) -> list[list[object]]:
    rows: list[list[object]] = []
    for index, week in enumerate(WEEKS):
        for plan, (start, growth, activation, per_user) in PLANS.items():
            active = round(start * (1 + growth) ** index * rng.uniform(0.97, 1.03))
            activated = round(active * activation * rng.uniform(0.92, 1.08))
            sessions = round(active * per_user * rng.uniform(0.94, 1.06))
            rows.append([week, plan, active, activated, sessions])
    return rows


def _account_sessions(rng: random.Random) -> list[list[object]]:
    rows: list[list[object]] = []
    account = 1000
    for plan, (accounts, median_sessions, median_minutes) in ACCOUNTS.items():
        for _ in range(accounts):
            account += 1
            sessions = max(1, round(rng.lognormvariate(math.log(median_sessions), 0.55)))
            minutes = max(0.5, rng.gauss(median_minutes, median_minutes * 0.28))
            rows.append([f"A{account}", plan, sessions, round(minutes, 1)])
    return rows


def _hourly_activity(rng: random.Random) -> list[list[object]]:
    rows: list[list[object]] = []
    for number, weekday in enumerate(WEEKDAYS, start=1):
        weekend = number >= 6
        for hour in range(24):
            # Two working-day peaks, late morning and mid afternoon.
            shape = math.exp(-((hour - 10.5) ** 2) / 8) + 0.85 * math.exp(
                -((hour - 15) ** 2) / 10
            )
            level = 40 + 520 * shape * (0.22 if weekend else 1.0)
            if number == 5 and hour >= 15:
                level *= 0.7
            rows.append([weekday, number, hour, round(level * rng.uniform(0.9, 1.1))])
    return rows


def _finance(rng: random.Random) -> list[list[object]]:
    rows: list[list[object]] = []
    for index, month in enumerate(MONTHS):
        # Bookings bunch up at each quarter end.
        quarter_end = 1.12 if month[-2:] in {"06", "09", "12", "03"} else 1.0
        for department, (start, growth, expense_ratio) in DEPARTMENTS.items():
            bookings = start * (1 + growth) ** index * quarter_end
            bookings = round(bookings * rng.uniform(0.95, 1.05), -2)
            # Spend tracks the trend, not the quarter-end bump.
            expenses = start * (1 + growth * 0.6) ** index * expense_ratio
            expenses = round(expenses * rng.uniform(0.96, 1.04), -2)
            rows.append([month, department, int(bookings), int(expenses)])
    return rows


def _invoices(rng: random.Random) -> list[list[object]]:
    rows: list[list[object]] = []
    invoice = 5000
    for segment, (invoices, median_amount, median_days, discount) in SEGMENTS.items():
        for _ in range(invoices):
            invoice += 1
            amount = rng.lognormvariate(math.log(median_amount), 0.5)
            days = max(1, round(rng.gauss(median_days, median_days * 0.3)))
            discount_pct = max(0.0, rng.gauss(discount, 1.5 + discount * 0.25))
            # A few invoices in every segment go badly overdue.
            if rng.random() < 0.04:
                days += rng.randint(30, 60)
            rows.append(
                [
                    f"INV-{invoice}",
                    rng.choice(MONTHS),
                    segment,
                    round(amount, 2),
                    round(discount_pct, 1),
                    days,
                ]
            )
    return rows


def _agent_runs(rng: random.Random) -> list[list[object]]:
    """One row per agent run: what an agent platform logs for each task."""
    rows: list[list[object]] = []
    run_number = 0
    for day in range(CLANKER_DAYS):
        today = CLANKER_START + timedelta(days=day)
        weekend = today.weekday() >= 5
        # A bad deploy of the code-review tools on one day, fixed the next.
        incident = today == CLANKER_START + timedelta(days=31)
        for agent, (start, growth, success, escalate, seconds, tools, models) in (
            CLANKER_AGENTS.items()
        ):
            level = start * (1 + growth) ** (day / 7) * (0.35 if weekend else 1.0)
            for _ in range(max(0, round(rng.gauss(level, level * 0.15)))):
                run_number += 1
                hour = _working_hour(rng, weekend)
                started = f"{today.isoformat()} {hour:02d}:{rng.randrange(60):02d}"
                model = _pick(rng, models)
                trigger = _pick(rng, CLANKER_TRIGGERS)
                ok = success - (0.35 if incident and agent == "Code Reviewer" else 0.0)
                roll = rng.random()
                if roll < ok:
                    outcome, error = "succeeded", ""
                elif roll < ok + escalate:
                    outcome, error = "escalated", ""
                else:
                    outcome = "failed"
                    error = (
                        "Tool timeout"
                        if incident and agent == "Code Reviewer"
                        else _pick(rng, CLANKER_ERRORS)
                    )
                duration = max(1.0, rng.lognormvariate(math.log(seconds), 0.45))
                calls = max(0, round(rng.gauss(tools, tools * 0.35)))
                tokens_in = round(duration * rng.uniform(90, 160) + calls * 400)
                tokens_out = round(tokens_in * rng.uniform(0.12, 0.3))
                price_in, price_out = CLANKER_MODELS[model]
                cost = (
                    CLANKER_RUN_FEE
                    + tokens_in / 1000 * price_in
                    + tokens_out / 1000 * price_out
                )
                rows.append(
                    [
                        f"run_{run_number:05d}", started, agent, model, trigger,
                        outcome, error, round(duration, 1), calls, tokens_in,
                        tokens_out, round(cost, 5),
                    ]
                )
    return rows


def _working_hour(rng: random.Random, weekend: bool) -> int:
    """An hour of the day, busiest late morning and mid afternoon (UTC)."""
    if rng.random() < (0.5 if weekend else 0.12):
        return rng.randrange(24)
    return min(23, max(0, round(rng.choice([10.5, 15.0]) + rng.gauss(0, 2.2))))


def _pick(rng: random.Random, weights: dict[str, float]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def _write(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


if __name__ == "__main__":
    main()
