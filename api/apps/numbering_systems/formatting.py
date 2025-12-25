from __future__ import annotations

import re
from datetime import datetime

TEMPLATE_TOKEN_RE = re.compile(r"\{(?:yyyy|yy|q|mm|m|n{1,9})}")


def render_template(*, template: str, count: int, effective_at: datetime) -> str:
    """Render a numbering system template for the provided count and date."""

    year_full = effective_at.year
    year_short = f"{year_full % 100:02}"
    quarter = (effective_at.month - 1) // 3 + 1
    month_full = f"{effective_at.month:02}"
    month_short = str(effective_at.month)

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        match token:
            case "{yyyy}":
                return str(year_full)
            case "{yy}":
                return year_short
            case "{q}":
                return str(quarter)
            case "{mm}":
                return month_full
            case "{m}":
                return month_short
            case t if t.startswith("{n") and t.endswith("}"):
                width = len(t) - 2
                return str(count + 1).zfill(width)
            case _:
                raise ValueError(f"Unknown numbering system token: {token!r}")

    return TEMPLATE_TOKEN_RE.sub(repl, template)
