from django import template

register = template.Library()


@register.filter
def format_tax_id_type(value: str) -> str:
    return value.replace("_", " ").upper()
