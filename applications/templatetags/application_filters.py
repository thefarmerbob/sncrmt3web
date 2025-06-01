from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def div(value, arg):
    """Divides the value by the argument"""
    try:
        return Decimal(str(value)) / Decimal(str(arg))
    except (ValueError, TypeError, ZeroDivisionError):
        return value 