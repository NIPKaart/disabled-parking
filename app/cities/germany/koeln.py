"""Map Köln's complete public disabled-parking layer to municipal deliveries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from koeln import StadtKoeln
from koeln.exceptions import ODPKoelnError
from koeln.koeln import NRW_PARKING_URL

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
            if result.source_url not in (None, NRW_PARKING_URL):
                message = "Unrecognized Köln distribution"
                raise SourceError(message)
            records = [
                self.normalize(item, nrw=result.source_url is not None)
                for item in result.records
            ]
            if result.source_url is not None:
                for record in records:
                    record["source_attributes"] = {
                        "distribution_url": result.source_url,
                        "publication_time": result.source_version,
                        "record": record["source_attributes"],
                    }
        except (ODPKoelnError, TimeoutError, ValueError, TypeError, KeyError) as error:
            message = "Köln source retrieval or mapping failed"
            raise SourceError(message) from error
        records.sort(key=lambda record: record["external_id"])
        return Collection(
            records, result.total_count, result.pages_fetched, result.complete
        )

    @staticmethod
    def normalize(item: ParkingRecord, *, nrw: bool = False) -> dict[str, Any]:
        """Keep original IDs, nullable capacity and literal source claims."""
        attributes = item.source_attributes
        if (
            isinstance(item.id, bool)
            or not isinstance(item.id, int)
            or item.id < 1
            or attributes.get("id")
            != (f"parking-disabled-koeln-{item.id}" if nrw else item.id)
        ):
            message = "Invalid Köln source identity"
            raise ValueError(message)
        number = attributes.get("numberOfSpaces" if nrw else "anzahl")
        if number is not None and (
            isinstance(number, bool) or not isinstance(number, int)
        ):
            message = "Invalid Köln capacity"
            raise ValueError(message)
        return {
            "external_id": str(item.id),
            "geometry": item.geometry,
            "number": capacity(number),
            "street": None,
            "access_category": "general",
            "orientation": None,
            "source_attributes": attributes.copy(),
            "source_updated_at": None,
        }
