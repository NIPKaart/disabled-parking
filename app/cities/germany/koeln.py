"""Map Köln's complete public disabled-parking layer to municipal deliveries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from koeln import StadtKoeln
from koeln.exceptions import ODPKoelnError

from app.cities import City
from app.records import Collection, SourceError, capacity

if TYPE_CHECKING:
    from koeln import ParkingRecord


class Municipality(City):
    """Retain source points and aggregate capacity without inventing bay geometry."""

    def __init__(self) -> None:
        """Initialize the municipal wrapper without the legacy telephone identity."""
        super().__init__(name="Köln", country="Germany", geo_code="DE-NW")

    async def collect(self) -> Collection:
        """Use package-owned count, pagination, identity and consistency checks."""
        try:
            async with StadtKoeln() as client:
                result = await client.parking_collection()
            records = [self.normalize(item) for item in result.records]
        except (ODPKoelnError, TimeoutError, ValueError, TypeError, KeyError) as error:
            message = "Köln source retrieval or mapping failed"
            raise SourceError(message) from error
        records.sort(key=lambda record: record["external_id"])
        return Collection(
            records, result.total_count, result.pages_fetched, result.complete
        )

    @staticmethod
    def normalize(item: ParkingRecord) -> dict[str, Any]:
        """Keep original IDs, nullable capacity and literal source claims."""
        attributes = item.source_attributes
        if (
            isinstance(item.entry_id, bool)
            or not isinstance(item.entry_id, int)
            or item.entry_id < 1
            or attributes.get("id") != item.entry_id
        ):
            message = "Invalid Köln source identity"
            raise ValueError(message)
        number = attributes.get("anzahl")
        if number is not None and (
            isinstance(number, bool) or not isinstance(number, int)
        ):
            message = "Invalid Köln capacity"
            raise ValueError(message)
        return {
            "external_id": str(item.entry_id),
            "geometry": item.geometry,
            "number": capacity(number),
            "street": None,
            "access_category": "general",
            "orientation": None,
            "source_attributes": attributes.copy(),
            "source_updated_at": None,
        }
