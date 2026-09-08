"""General class for cities."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.records import MunicipalRecord


class City:
    """General class for cities."""

    def __init__(
        self,
        name: str,
        country: str,
        geo_code: str,
    ) -> None:
        """Initialize the class."""
        self.name = name
        self.country = country
        self.geo_code = geo_code

    @property
    def source_id(self) -> str:
        """Reuse the existing geographic prefix without database primary keys."""
        code = getattr(self, "cbs_code", None) or getattr(self, "phone_code", None)
        if code is None:
            raise ValueError(self.name)
        return f"{self.geo_code}-{code}"

    def normalize(self, item: object) -> "MunicipalRecord":
        """Translate one source item without fetching or writing anything."""
        raise NotImplementedError(type(item))

    def source_items(self, payload: dict) -> list:
        """Parse a captured response using this source's existing package model."""
        raise NotImplementedError(type(payload))
