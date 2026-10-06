"""Map Namur's complete public-road PMR selection without losing source context."""

import math
from datetime import date
from typing import Any

from namur import ODPNamur, ParkingSpot, ParkingType
from namur.exceptions import ODPNamurError

from app.cities import City
from app.records import Collection, SourceError


class Municipality(City):
    """Collect source claims; core approves the source and reviews publication."""

    def __init__(self) -> None:
        """Initialize the existing municipal wrapper."""
        super().__init__(name="Namur", country="Belgium", geo_code="BE-WNA")
        self.phone_code = "03281"

    async def async_get_locations(self) -> list[ParkingSpot]:
        """Retain the existing inspection path with the package's typed PMR filter."""
        async with ODPNamur() as client:
            return await client.parking_spaces(limit=1000, parking_type=ParkingType.PMR)

    async def collect(self) -> Collection:
        """Use the public package snapshot API for pagination and completeness."""
        try:
            async with ODPNamur() as client:
                snapshot = await client.parking_snapshot(parking_type=ParkingType.PMR)
            records = [self.normalize(item) for item in snapshot.records]
        except (ODPNamurError, TimeoutError, ValueError, TypeError, KeyError) as error:
            message = "Namur source retrieval or mapping failed"
            raise SourceError(message) from error
        records.sort(key=lambda record: record["external_id"])
        return Collection(
            records,
            total_count=snapshot.total_count,
            pages_fetched=snapshot.pages_fetched,
            complete=snapshot.complete,
        )

    def normalize(self, item: ParkingSpot) -> dict[str, Any]:
        """Preserve original IDs, Points, source dates and parking-zone context."""
        source = item.source_attributes
        if (
            not isinstance(item.spot_id, str)
            or not item.spot_id
            or len(item.spot_id) > 255
            or item.spot_id != item.spot_id.strip()
            or source.get("identifiant") != item.spot_id
        ):
            message = "Invalid Namur source ID"
            raise ValueError(message)
        if item.parking_type != ParkingType.PMR or source.get("type_parking") != "PMR":
            message = "Unexpected Namur parking category"
            raise ValueError(message)
        geometry = source.get("geo_shape")
        if not isinstance(geometry, dict):
            message = "Expected the original Namur geometry"
            raise TypeError(message)
        point = geometry.get("coordinates")
        if (
            geometry.get("type") != "Point"
            or not isinstance(point, list)
            or len(point) != 2
        ):
            message = "Expected a Namur WGS84 Point"
            raise ValueError(message)
        for value, bound in zip(point, (180, 90), strict=True):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not -bound <= value <= bound
            ):
                message = "Invalid Namur WGS84 coordinate"
                raise ValueError(message)
        street = item.street
        if street is not None and (not isinstance(street, str) or len(street) > 255):
            message = "Invalid Namur street"
            raise ValueError(message)
        modified = source.get("date_modif")
        if modified is not None and (
            not isinstance(modified, str)
            or len(modified) != 10
            or date.fromisoformat(modified).isoformat() != modified
        ):
            message = "Invalid Namur source modification date"
            raise ValueError(message)
        return {
            "external_id": item.spot_id,
            "geometry": geometry,
            "number": None,
            "street": street,
            "access_category": "general",
            "orientation": None,
            "source_attributes": source,
            "source_updated_at": modified,
        }
