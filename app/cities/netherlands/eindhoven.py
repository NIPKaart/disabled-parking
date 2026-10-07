"""Collect Eindhoven's declared disabled-parking selection for source review."""

from __future__ import annotations

import math
from typing import Any

from eindhoven import ODPEindhoven, ParkingSpot, ParkingType
from eindhoven.exceptions import ODPEindhovenError

from app.cities import City
from app.records import Collection, SourceError, capacity

PARKING_TYPE = "Parkeerplaats Gehandicapten"
MAX_RECORDS = 9900


class Municipality(City):
    """Preserve source values without claiming unverified general access."""

    def __init__(self) -> None:
        """Initialize the existing municipality identity."""
        super().__init__(name="Eindhoven", country="Netherlands", geo_code="NL-NB")
        self.cbs_code = "0772"

    async def collect(self) -> Collection:
        """Map a complete selection retrieved and verified by the source package."""
        try:
            async with ODPEindhoven() as client:
                collection = await client.parking_collection(
                    parking_type=ParkingType.DISABLED_PARKING,
                    max_records=MAX_RECORDS,
                )
            normalized = [
                self.normalize_collection_record(item) for item in collection.records
            ]
        except (
            ODPEindhovenError,
            TimeoutError,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            msg = "Eindhoven source retrieval or mapping failed"
            raise SourceError(msg) from error
        return Collection(
            normalized,
            collection.total_count,
            collection.pages_fetched,
            collection.complete,
        )

    def normalize_collection_record(self, item: ParkingSpot) -> dict[str, Any]:
        """Check source identity while mapping a package record to NIPKaart."""
        record = self.normalize(item.source_attributes)
        if item.spot_id != record["external_id"]:
            msg = "Eindhoven package ID differs from the original objectid"
            raise ValueError(msg)
        return record

    def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Retain original object IDs and Points; unknown access stays unknown."""
        object_id = item["objectid"]
        if (
            not isinstance(object_id, int)
            or isinstance(object_id, bool)
            or object_id <= 0
        ):
            msg = "Invalid Eindhoven objectid"
            raise ValueError(msg)
        if item["type_en_merk"] != PARKING_TYPE:
            msg = "Unexpected Eindhoven parking category"
            raise ValueError(msg)
        geometry = item["geo_shape"]["geometry"]
        if not isinstance(geometry, dict):
            msg = "Expected an Eindhoven geometry object"
            raise TypeError(msg)
        point = geometry.get("coordinates")
        if (
            geometry.get("type") != "Point"
            or not isinstance(point, list)
            or len(point) != 2
        ):
            msg = "Expected an Eindhoven WGS84 Point"
            raise ValueError(msg)
        for value, bound in zip(point, (180, 90), strict=True):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not -bound <= value <= bound
            ):
                msg = "Invalid Eindhoven WGS84 coordinate"
                raise ValueError(msg)
        street = item["straat"]
        if street is not None and (not isinstance(street, str) or len(street) > 255):
            msg = "Invalid Eindhoven street"
            raise ValueError(msg)
        return {
            "external_id": str(object_id),
            "geometry": geometry,
            "number": capacity(item["aantal"]),
            "street": street,
            "access_category": "unknown",
            "orientation": None,
            "source_attributes": item.copy(),
            "source_updated_at": None,
        }
