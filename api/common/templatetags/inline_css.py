from __future__ import annotations

from pathlib import Path

from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def inline_css(static_path: str) -> str:
    """
    Read a CSS file resolved by Django staticfiles finders and emit it as
    an inline <style> tag.

    Usage:
        {% inline_css "app/styles.css" %}
    """
    path = finders.find(static_path)
    if not path:
        raise template.TemplateSyntaxError(f"Static file not found: {static_path}")

    with Path(path).open(encoding="utf-8") as f:
        css = f.read()

    return mark_safe(f"<style>\n{css}\n</style>")  # noqa: S308
