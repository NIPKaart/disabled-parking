"""Fetch and map the agreed Amsterdam general accessible-parking selection."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from odp_amsterdam import ODPAmsterdam
from odp_amsterdam.exceptions import ODPAmsterdamError

from app.cities import City
from app.records import Collection, SourceError, capacity

if TYPE_CHECKING:
    from odp_amsterdam.models import ParkingLocations, ParkingSpot

MAX_RECORDS = 10000


def validate_geometry(geometry: dict[str, Any]) -> None:
    """Check bounded WGS84 Polygon rings; core checks topology with PostGIS."""
    rings = geometry.get("coordinates")
    if geometry.get("type") != "Polygon" or not isinstance(rings, list) or not rings:
        msg = "Expected a Polygon with coordinates"
        raise ValueError(msg)
    if any(not isinstance(ring, list) for ring in rings):
        msg = "Polygon rings must be lists of positions"
        raise ValueError(msg)
    if len(rings) > 100 or sum(len(ring) for ring in rings) > 10000:
        msg = "Polygon exceeds pilot geometry limits"
        raise ValueError(msg)
    for ring in rings:
        if len(ring) < 4 or ring[0] != ring[-1]:
            msg = "Polygon rings must be closed and have at least four positions"
            raise ValueError(msg)
        for point in ring:
            if not isinstance(point, list) or len(point) != 2:
                msg = "Expected longitude/latitude positions"
                raise ValueError(msg)
            for value, bound in zip(point, (180, 90), strict=True):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or not -bound <= value <= bound
                ):
                    msg = "Invalid WGS84 coordinate"
                    raise ValueError(msg)


class Municipality(City):
    """One source selection; no publication or point derivation in the collector."""

    def __init__(self) -> None:
        """Initialize the existing municipality identity."""
        super().__init__(name="Amsterdam", country="Netherlands", geo_code="NL-NH")
        self.cbs_code = "0363"

    async def async_get_locations(self) -> ParkingLocations:
        """Let the universal package retrieve and verify the bounded selection."""
        async with ODPAmsterdam() as client:
            return await client.locations(limit=MAX_RECORDS + 1, parking_type="E6a")

    async def collect(self) -> Collection:
        """Adapt the package response to the shared normalized delivery model."""
        try:
            result = await self.async_get_locations()
        except ODPAmsterdamError as error:
            msg = "Amsterdam source request failed"
            raise SourceError(msg) from error
        return Collection(
            records=[self.normalize(item) for item in result.records],
            total_count=result.total_count,
            pages_fetched=result.pages_fetched,
            complete=result.complete,
        )

    def normalize(self, item: ParkingSpot) -> dict[str, Any]:
        """Preserve source claims and fail if any regime leaves the agreed scope."""
        if (
            not isinstance(item.spot_id, str)
            or not item.spot_id
            or item.spot_id != item.spot_id.strip()
        ):
            msg = "Missing or invalid source ID"
            raise ValueError(msg)
        if (
            item.spot_type != "E6a"
            or not item.regimes
            or any(
                regime.get("eType") != "E6a"
                or regime.get("eTypeDescription")
                != "Gehandicaptenparkeerplaats algemeen"
                or regime.get("kenteken") not in (None, "")
                for regime in item.regimes
            )
        ):
            msg = f"Unexpected parking scope for {item.spot_id}"
            raise ValueError(msg)
        validate_geometry(item.geometry)
        return {
            "external_id": item.spot_id,
            "geometry": item.geometry,
            "number": capacity(item.number),
            "street": item.street,
            "access_category": "general",
            "source_attributes": {
                "regimes": item.regimes,
                "orientation": item.orientation,
                "version_date": (
                    item.version_date.isoformat() if item.version_date else None
                ),
            },
            "source_updated_at": None,
        }
