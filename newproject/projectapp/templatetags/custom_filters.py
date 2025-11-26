# projectapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """
    Multiply value by arg and return formatted number (no extra decimals if integer).
    Usage: {{ order.quantity|mul:order.product.price }}
    """
    try:
        v = float(value)
        a = float(arg)
        res = v * a
        # if integer-like, show without .0
        if abs(res - int(res)) < 0.000001:
            return str(int(res))
        # else show 2 decimals
        return f"{res:.2f}"
    except Exception:
        return ""