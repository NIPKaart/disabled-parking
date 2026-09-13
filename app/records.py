"""Validate the capacity supplied by a source without losing information."""

from decimal import Decimal, InvalidOperation


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
