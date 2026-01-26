from __future__ import annotations

from django.db import DataError
from psycopg.errors import NumericValueOutOfRange

NUMERIC_OUT_OF_RANGE_SQLSTATE = "22003"


def is_numeric_out_of_range_error(error: DataError) -> bool:
    for exc in (error, error.__cause__, error.__context__):
        if exc is None:
            continue

        if isinstance(exc, NumericValueOutOfRange):
            return True

        sqlstate = getattr(exc, "sqlstate", None) or getattr(exc, "pgcode", None) or getattr(exc, "code", None)
        if sqlstate == NUMERIC_OUT_OF_RANGE_SQLSTATE:
            return True

    return False
