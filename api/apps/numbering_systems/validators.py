import re

from rest_framework import serializers

ALLOWED_TOKENS = {"{yyyy}", "{yy}", "{q}", "{mm}", "{m}"}
N_TOKEN_RE = re.compile(r"\{n{1,9}}")
TOKEN_RE = re.compile(r"\{[^{}]*}")
ALLOWED_FMT_RE = re.compile(r"(?:[^{}]|\{(?:yyyy|yy|q|mm|m|n{1,9})})+$")


def numbering_system_template_validator(value: str) -> None:
    if not ALLOWED_FMT_RE.fullmatch(value):
        # Try to produce a nice error message
        unknown = []
        for m in TOKEN_RE.finditer(value):
            token = m.group(0)
            if token not in ALLOWED_TOKENS and not N_TOKEN_RE.fullmatch(token):
                unknown.append(token)

        if unknown:
            raise serializers.ValidationError(
                f"Unknown placeholder(s): {', '.join(unknown)}. "
                "Allowed: {yyyy}, {yy}, {q}, {mm}, {m}, and {n...} (1-9 n's)."
            )

        # Otherwise it's probably stray / unmatched braces
        raise serializers.ValidationError("Unmatched or stray braces in format.")
