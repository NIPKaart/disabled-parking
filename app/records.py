"""Shared municipal output, independent of database and file storage."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date, datetime


def text(value: object) -> str | None:
    """Preserve unknown text instead of emitting the string None."""
    return None if value is None else str(value).strip() or None


def identifier(value: object) -> str:
    """Preserve complete string IDs and reject ambiguous numeric identifiers."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError(value)
    result = str(value)
    if not result or result != result.strip():
        raise ValueError(value)
    return result


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


def orientation(value: object) -> str | None:
    """Use the same spelling for the orientation mappings already in the adapters."""
    name = text(value)
    return {"Dwars": "Haaks", "Schuin": "Visgraat", "Vissengraat": "Visgraat"}.get(
        name,
        name,
    )


@dataclass(frozen=True, kw_only=True)
class MunicipalRecord:
    """One source statement; neither visibility nor publication is decided here."""

    external_id: str
    legacy_id: str
    latitude: float
    longitude: float
    number: int | None
    street: str | None = None
    orientation: str | None = None
    geometry_method: str = "source_point"
    identity_method: str = "source_id"
    source_created_at: datetime | date | None = None
    source_updated_at: datetime | date | None = None
    source_attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Reject malformed records before they reach any output writer."""
        identifier(self.external_id)
        identifier(self.legacy_id)
        if (
            not math.isfinite(self.latitude)
            or not -90 <= self.latitude <= 90
            or not math.isfinite(self.longitude)
            or not -180 <= self.longitude <= 180
        ):
            raise ValueError((self.latitude, self.longitude))
        if self.number is not None and (
            isinstance(self.number, bool)
            or not isinstance(self.number, int)
            or self.number < 0
        ):
            raise ValueError(self.number)
