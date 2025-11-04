from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply two numbers in Django templates"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''