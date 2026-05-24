from glyf.dashboard import components as c


def product_owner() -> c.ComponentSpec:
    return c.label_value("Owner", "Product Analytics")


def activation_health(rate: float) -> c.ComponentSpec:
    if rate >= 0.8:
        return c.alert("Activation is tracking above target.", title="Health", tone="success")
    return c.alert("Activation needs attention.", title="Health", tone="warning")
