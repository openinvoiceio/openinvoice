from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db import connection

GROSS_REVENUE_SQL = """
WITH bounds AS (
  SELECT
    %(date_after)s::date AS start_month,
    %(date_before)s::date AS end_month
),
months AS (
  SELECT gs::date AS month_start
  FROM bounds b,
  LATERAL generate_series(b.start_month, b.end_month, interval '1 month') AS gs
),
base AS (
  SELECT
    date_trunc('month', i.issue_date)::date AS month_start,
    i.currency,
    SUM(i.total_amount) AS total_amount,
    COUNT(*)            AS invoice_count
  FROM invoices_invoice i
  WHERE
    i.account_id = %(account_id)s
    AND i.status = 'paid'
    AND i.currency = %(currency)s
    AND i.issue_date >= %(date_after)s::date
    AND i.issue_date <  (%(date_before)s::date + INTERVAL '1 day')
    AND (%(customer_id)s IS NULL OR i.customer_id = %(customer_id)s)
  GROUP BY 1, 2
),
currencies AS (
  SELECT %(currency)s::text AS currency
)
SELECT
  m.month_start                        AS date,
  c.currency                           AS currency,
  COALESCE(b.total_amount, 0)::numeric AS total_amount,
  COALESCE(b.invoice_count, 0)::int    AS invoice_count
FROM months m
CROSS JOIN currencies c
LEFT JOIN base b
  ON b.month_start = m.month_start AND b.currency = c.currency
ORDER BY m.month_start, c.currency;
"""


def fetch_gross_revenue(
    *,
    account_id: UUID,
    currency: str,
    date_after: date | None = None,
    date_before: date | None = None,
    customer_id: UUID | None = None,
) -> list[dict]:
    params: dict[str, str | UUID | date | None] = {
        "account_id": account_id,
        "currency": currency,
        "date_after": date_after,
        "date_before": date_before,
        "customer_id": customer_id,
    }
    with connection.cursor() as cur:
        cur.execute(GROSS_REVENUE_SQL, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]


OVERDUE_BALANCE_SQL = """
WITH bounds AS (
  SELECT
    %(date_after)s::date AS start_month,
    %(date_before)s::date AS end_month
),
months AS (
  SELECT gs::date AS month_start
  FROM bounds b,
  LATERAL generate_series(b.start_month, b.end_month, interval '1 month') AS gs
),
base AS (
  SELECT
    date_trunc('month', i.due_date)::date AS month_start,
    i.currency,
    SUM(i.total_amount)      AS total_amount,
    COUNT(*)                 AS invoice_count,
    array_agg(i.id)          AS invoice_ids
  FROM invoices_invoice i
  WHERE
    i.account_id = %(account_id)s
    AND i.status = 'open'
    AND i.currency = %(currency)s
    AND i.due_date < %(today)s::date
    AND i.due_date >= %(date_after)s::date
    AND i.due_date <  (%(date_before)s::date + INTERVAL '1 day')
    AND (%(customer_id)s IS NULL OR i.customer_id = %(customer_id)s)
  GROUP BY 1, 2
),
currencies AS (
  SELECT %(currency)s::text AS currency
)
SELECT
  m.month_start                                     AS date,
  c.currency                                        AS currency,
  COALESCE(b.total_amount, 0)::numeric              AS total_amount,
  COALESCE(b.invoice_count, 0)::int                 AS invoice_count,
  COALESCE(b.invoice_ids, '{}'::uuid[])::uuid[]     AS invoice_ids
FROM months m
CROSS JOIN currencies c
LEFT JOIN base b
  ON b.month_start = m.month_start AND b.currency = c.currency
ORDER BY m.month_start, c.currency;
"""


def fetch_overdue_balance(
    *,
    account_id: UUID,
    currency: str,
    today: date,
    date_after: date | None = None,
    date_before: date | None = None,
    customer_id: UUID | None = None,
) -> list[dict]:
    params: dict[str, str | UUID | date | None] = {
        "account_id": account_id,
        "currency": currency,
        "today": today,
        "date_after": date_after,
        "date_before": date_before,
        "customer_id": customer_id,
    }
    with connection.cursor() as cur:
        cur.execute(OVERDUE_BALANCE_SQL, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]
