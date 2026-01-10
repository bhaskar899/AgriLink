from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply (x * y)"""
    try:
        return float(value) * float(arg)
    except:
        return 0

@register.filter
def div(value, arg):
    """Divide (x / y)"""
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except:
        return 0