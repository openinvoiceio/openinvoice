import base64
from datetime import date, datetime, timedelta

from django import template
from django.utils import timezone

from apps.files.models import File

register = template.Library()


@register.simple_tag
def encode_logo_base64(file: File | None) -> str:
    """
    A template tag that returns an encoded string representation of a logo file
    Usage::
        {% encode_logo_base64 file %}
    """
    if not file:
        return ""

    try:
        file_str = base64.b64encode(file.data.read()).decode("utf-8")
        return f"data:{file.content_type};base64,{file_str}"
    except (FileNotFoundError, OSError, ValueError, AttributeError, TypeError):
        return ""


@register.filter
def due_from_term(value: int) -> datetime | date:
    return timezone.now() + timedelta(days=value)
