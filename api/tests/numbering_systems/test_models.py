from datetime import UTC, datetime

import pytest

from apps.numbering_systems.enums import NumberingSystemResetInterval
from tests.factories import NumberingSystemFactory

pytestmark = pytest.mark.django_db


def test_render_numbering_system_renders_all_supported_tokens():
    numbering_system = NumberingSystemFactory(template="{yyyy}-{yy}-{q}-{mm}-{m}-{n}-{nn}-{nnn}")
    effective_at = datetime(2024, 4, 15, 10, tzinfo=UTC)

    rendered = numbering_system.render_number(count=0, effective_at=effective_at)

    assert rendered == "2024-24-2-04-4-1-01-001"


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, "INV-001"),
        (999, "INV-1000"),
    ],
)
def test_render_numbering_system_sequence_padding_and_overflow(count: int, expected: str):
    numbering_system = NumberingSystemFactory(template="INV-{nnn}")
    effective_at = datetime(2024, 1, 1, tzinfo=UTC)

    rendered = numbering_system.render_number(count=count, effective_at=effective_at)

    assert rendered == expected


def test_render_numbering_system_supports_mixed_tokens_and_static_text():
    numbering_system = NumberingSystemFactory(template="INV{yy}{mm}-{nn}/Q{q}")
    effective_at = datetime(2024, 4, 15, tzinfo=UTC)

    rendered = numbering_system.render_number(count=4, effective_at=effective_at)

    assert rendered == "INV2404-05/Q2"


def test_render_numbering_system_invalid_token_raises_error():
    numbering_system = NumberingSystemFactory(template="{bad}-{nn}")
    effective_at = datetime(2024, 4, 15, tzinfo=UTC)

    number = numbering_system.render_number(count=0, effective_at=effective_at)

    assert number == "{bad}-01"


@pytest.mark.parametrize(
    ("interval", "effective_at", "expected_start", "expected_end"),
    [
        (
            NumberingSystemResetInterval.NEVER,
            datetime(2024, 1, 15, 12, tzinfo=UTC),
            None,
            None,
        ),
        (
            NumberingSystemResetInterval.WEEKLY,
            datetime(2024, 6, 12, 15, tzinfo=UTC),
            datetime(2024, 6, 10, tzinfo=UTC),
            datetime(2024, 6, 17, tzinfo=UTC),
        ),
        (
            NumberingSystemResetInterval.MONTHLY,
            datetime(2024, 12, 5, 15, tzinfo=UTC),
            datetime(2024, 12, 1, tzinfo=UTC),
            datetime(2025, 1, 1, tzinfo=UTC),
        ),
        (
            NumberingSystemResetInterval.QUARTERLY,
            datetime(2024, 12, 5, 15, tzinfo=UTC),
            datetime(2024, 10, 1, tzinfo=UTC),
            datetime(2025, 1, 1, tzinfo=UTC),
        ),
        (
            NumberingSystemResetInterval.YEARLY,
            datetime(2024, 7, 5, 15, tzinfo=UTC),
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2025, 1, 1, tzinfo=UTC),
        ),
    ],
)
def test_calculate_numbering_system_bounds(interval, effective_at, expected_start, expected_end):
    numbering_system = NumberingSystemFactory(reset_interval=interval)

    start, end = numbering_system.calculate_bounds(effective_at=effective_at)

    assert start == expected_start
    assert end == expected_end
