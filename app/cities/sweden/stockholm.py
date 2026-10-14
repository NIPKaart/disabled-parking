"""Preserve Stockholm permit-holder regulations without inventing bay counts."""

import math
import os
from typing import Any

from odp_stockholm import ODPStockholmError, ParkingSpot, ParkingStockholm, ParkingType

from app.records import Collection, SourceError


def validate_lines(geometry: dict[str, Any]) -> None:
    """Reject empty lines, extra dimensions and invalid WGS84 positions."""
    coordinates = geometry.get("coordinates")
    lines = [coordinates] if geometry["type"] == "LineString" else coordinates
    if not isinstance(lines, list) or not lines:
        message = "Empty Stockholm geometry"
        raise ValueError(message)
    for line in lines:
        if not isinstance(line, list) or len(line) < 2:
            message = "Invalid Stockholm line"
            raise ValueError(message)
        for point in line:
            if not isinstance(point, list) or len(point) != 2:
                message = "Expected Stockholm WGS84 coordinates"
                raise ValueError(message)
            for value, bound in zip(point, (180, 90), strict=True):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or not -bound <= value <= bound
                ):
                    message = "Invalid Stockholm WGS84 coordinate"
                    raise ValueError(message)


class Municipality:
    """Map a complete package collection; core owns source and record approval."""

    async def collect(self) -> Collection:
        """Use the public package interface; missing credentials fail safely."""
        key = os.environ.get("STOCKHOLM_API_KEY", "").strip()
        if not key:
            message = "Stockholm requires STOCKHOLM_API_KEY"
            raise SourceError(message)
        try:
            async with ParkingStockholm(api_key=key) as client:
                result = await client.parking_collection(
                    parking_type=ParkingType.DISABLED
                )
            records = [self.normalize(item) for item in result.records]
        except ODPStockholmError, TimeoutError, ValueError, TypeError, KeyError:
            message = "Stockholm source retrieval or mapping failed"
            raise SourceError(message) from None
        records.sort(key=lambda record: record["external_id"])
        return Collection(
            records, result.total_count, result.pages_fetched, result.complete
        )

    def normalize(self, item: ParkingSpot) -> dict[str, Any]:
        """Keep feature IDs, original lines, validity and rule context unchanged."""
        source = item.source_attributes
        if (
            not isinstance(item.id, str)
            or not item.id.startswith("LTFR_P_RORELSEHINDRADE.")
            or len(item.id) > 255
            or item.id != item.id.strip()
            or source.get("id") != item.id
        ):
            message = "Invalid Stockholm source identity"
            raise ValueError(message)
        if source.get("type") != "Feature":
            message = "Expected a Stockholm source feature"
            raise ValueError(message)
        fid = source["properties"]["FID"]
        if (
            not isinstance(fid, int)
            or isinstance(fid, bool)
            or fid < 1
            or item.id != f"LTFR_P_RORELSEHINDRADE.{fid}"
        ):
            message = "Inconsistent Stockholm source identity"
            raise ValueError(message)
        if source["properties"].get("VF_PLATS_TYP") not in {
            None,
            "Reserverad p-plats rörelsehindrad",
        }:
            message = "Unexpected Stockholm parking category"
            raise ValueError(message)
        geometry = source.get("geometry")
        if not isinstance(geometry, dict) or geometry != item.geometry:
            message = "Expected the original Stockholm geometry"
            raise ValueError(message)
        if geometry.get("type") not in {"LineString", "MultiLineString"}:
            message = "Expected Stockholm line geometry"
            raise ValueError(message)
        validate_lines(geometry)
        if item.street is not None and (
            not isinstance(item.street, str) or len(item.street) > 255
        ):
            message = "Invalid Stockholm street"
            raise ValueError(message)
        return {
            "external_id": item.id,
            "geometry": geometry,
            "number": None,
            "street": item.street,
            "access_category": "unknown",
            "orientation": None,
            "source_attributes": source,
            "source_updated_at": None,
        }
