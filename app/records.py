"""Validate the capacity supplied by a source without losing information."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


class SourceError(Exception):
    """A source request failed before a complete selection could be collected."""


def capacity(value: object) -> int | None:
    """Keep unknown separate from zero and reject lossy integer coercion."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError(value)
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(value) from error
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise ValueError(value)
    return int(number)


@dataclass
class Collection:
    """Normalized source claims accompanied by source completeness evidence."""

    records: list[dict[str, Any]]
    total_count: int
    pages_fetched: int
    complete: bool
