"""Map Antwerpen's complete identified selection without losing restrictions."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from antwerpen import ODPAntwerpen
from antwerpen.exceptions import ODPAntwerpenError

from app.cities import City
from app.records import Collection, SourceError

if TYPE_CHECKING:
    from antwerpen import ParkingRecord

SELECTION_FILTER = "GISID IS NOT NULL AND GISID <> ''"


class Municipality(City):
    """Collect original source claims for approval and review in core."""

    def __init__(self) -> None:
        """Initialize the existing municipal wrapper."""
        super().__init__(name="Antwerpen", country="Belgium", geo_code="BE-VAN")

    async def collect(self) -> Collection:
        """Retrieve all identified records, with package-owned completeness checks."""
        try:
            async with ODPAntwerpen() as client:
                result = await client.parking_collection(set_filter=SELECTION_FILTER)
            records = [self.normalize(item) for item in result.records]
        except (
            ODPAntwerpenError,
            TimeoutError,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            message = "Antwerpen source retrieval or mapping failed"
            raise SourceError(message) from error
        records.sort(key=lambda record: record["external_id"])
        return Collection(
            records, result.total_count, result.pages_fetched, result.complete
        )

    def normalize(self, item: ParkingRecord) -> dict[str, Any]:
        """Retain GIS IDs, all polygon rings, capacity and restricted-access claims."""
        attributes = item.source_attributes
        if (
            not isinstance(item.gis_id, str)
            or not item.gis_id
            or len(item.gis_id) > 255
            or item.gis_id != item.gis_id.strip()
            or attributes.get("GISID") != item.gis_id
        ):
            message = "Invalid Antwerpen GIS identity"
            raise ValueError(message)
        if attributes.get("STATUS") != "actief":
            message = "Unexpected Antwerpen parking status"
            raise ValueError(message)
        geometry = item.geometry
        if not isinstance(geometry, dict) or geometry.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            message = "Expected original Antwerpen WGS84 polygons"
            raise ValueError(message)
        coordinates = geometry.get("coordinates")
        polygons = [coordinates] if geometry["type"] == "Polygon" else coordinates
        if not isinstance(polygons, list) or not polygons:
            message = "Missing Antwerpen polygon coordinates"
            raise ValueError(message)
        for polygon in polygons:
            self.validate_polygon(polygon)
        number = attributes.get("Capaciteit")
        if number is not None and (
            isinstance(number, bool) or not isinstance(number, int) or number < 0
        ):
            message = "Invalid Antwerpen capacity"
            raise ValueError(message)
        return {
            "external_id": item.gis_id,
            "geometry": geometry,
            "number": number,
            "street": None,
            "access_category": "unknown",
            "orientation": {
                "Langs": "parallel",
                "Dwars": "perpendicular",
                "Schuin": "angle",
            }.get(attributes.get("Orientatie")),
            "source_attributes": attributes.copy(),
            "source_updated_at": None,
        }

    @staticmethod
    def validate_polygon(polygon: Any) -> None:
        """Reject malformed WGS84 rings before the shared bounds validation."""
        if not isinstance(polygon, list) or not polygon:
            message = "Missing Antwerpen polygon rings"
            raise ValueError(message)
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                message = "Invalid Antwerpen polygon ring"
                raise ValueError(message)
            for point in ring:
                if not isinstance(point, list) or len(point) != 2:
                    message = "Invalid Antwerpen polygon position"
                    raise ValueError(message)
                for value, bound in zip(point, (180, 90), strict=True):
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                        or not -bound <= value <= bound
                    ):
                        message = "Invalid Antwerpen WGS84 coordinate"
                        raise ValueError(message)
