"""Map Arnhem's complete E6a selection to municipal source claims."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from arnhem import ODPArnhem
from arnhem.exceptions import ODPArnhemError

from app.cities import City
from app.records import Collection, SourceError

if TYPE_CHECKING:
    from arnhem import ParkingRecord

SELECTION_FILTER = "RVV_SOORT='E6a'"


class Municipality(City):
    """Preserve full polygons and extra signage for source review."""

    def __init__(self) -> None:
        """Initialize Arnhem's existing municipality identity."""
        super().__init__(name="Arnhem", country="Netherlands", geo_code="NL-GE")
        self.cbs_code = "0202"

    async def collect(self) -> Collection:
        """Retrieve a count/ID-verified selection through the source package."""
        try:
            async with ODPArnhem() as client:
                result = await client.parking_collection(set_filter=SELECTION_FILTER)
            records = [self.normalize(item) for item in result.records]
        except (ODPArnhemError, TimeoutError, ValueError, TypeError, KeyError) as error:
            msg = "Arnhem source retrieval or mapping failed"
            raise SourceError(msg) from error
        records.sort(key=lambda record: record["external_id"])
        return Collection(
            records, result.total_count, result.pages_fetched, result.complete
        )

    def normalize(self, item: ParkingRecord) -> dict[str, Any]:
        """Keep asset IDs, source geometry and unknown capacity and source dates."""
        attributes = item.source_attributes
        if (
            isinstance(item.spot_id, bool)
            or not isinstance(item.spot_id, int)
            or item.spot_id <= 0
            or attributes.get("ID") != item.spot_id
            or attributes.get("OBJECTID") != item.object_id
        ):
            msg = "Invalid Arnhem source identity"
            raise ValueError(msg)
        if attributes.get("RVV_SOORT") != "E6a":
            msg = "Unexpected Arnhem parking category"
            raise ValueError(msg)
        street, sign = attributes.get("STRAAT"), attributes.get("BORD")
        if street is not None and (not isinstance(street, str) or len(street) > 255):
            msg = "Invalid Arnhem street"
            raise ValueError(msg)
        if sign is not None and not isinstance(sign, str):
            msg = "Invalid Arnhem additional signage"
            raise TypeError(msg)
        return {
            "external_id": str(item.spot_id),
            "geometry": item.geometry,
            "number": None,
            "street": street,
            "access_category": "unknown" if sign and sign.strip() else "general",
            "orientation": None,
            "source_attributes": attributes.copy(),
            "source_updated_at": None,
        }
