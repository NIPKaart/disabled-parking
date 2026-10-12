"""Collect Groningen's general disabled bays without manufacturing stable IDs."""

from __future__ import annotations

import json
import math
from typing import Any

import aiohttp

from app.cities import City
from app.records import Collection, SourceError

SOURCE_URL = "https://maps.groningen.nl/geoserver/geo_info/ows"
FEATURE_TYPE = "geo_info:Parkeervakken gemeente Groningen"
SELECTION_FILTER = "TYPE='gehandicapten algemeen' AND ETYPE='E06'"
MAX_RECORDS = 10000
ORIENTATIONS = {"langsparkeren": "parallel", "haaksparkeren": "perpendicular"}


class Municipality(City):
    """Deliver original source claims; core reconciles changing feature IDs."""

    def __init__(self) -> None:
        """Initialize Groningen's municipality identity."""
        super().__init__(name="Groningen", country="Netherlands", geo_code="NL-GR")
        self.cbs_code = "0014"

    @staticmethod
    async def request(client: aiohttp.ClientSession) -> dict[str, Any]:
        """Fetch the whole bounded selection in one response, without paging ties."""
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": FEATURE_TYPE,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "count": MAX_RECORDS,
            "CQL_FILTER": SELECTION_FILTER,
        }
        async with client.get(SOURCE_URL, params=params) as response:
            response.raise_for_status()
            result = await response.json()
        if not isinstance(result, dict):
            message = "Expected a Groningen FeatureCollection"
            raise TypeError(message)
        return result

    def parse(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Reject truncated, empty or malformed selections and duplicate IDs."""
        total, features = data["numberMatched"], data["features"]
        if (
            data.get("type") != "FeatureCollection"
            or isinstance(total, bool)
            or not isinstance(total, int)
            or not 0 < total <= MAX_RECORDS
        ):
            message = "Invalid Groningen selection count"
            raise ValueError(message)
        if (
            not isinstance(features, list)
            or len(features) != total
            or data["numberReturned"] != total
            or isinstance(data["numberReturned"], bool)
            or not isinstance(data["numberReturned"], int)
        ):
            message = "Incomplete or invalid Groningen selection"
            raise ValueError(message)
        if data["crs"]["properties"]["name"] != "urn:ogc:def:crs:EPSG::4326":
            message = "Unexpected Groningen coordinate system"
            raise ValueError(message)
        records = [self.normalize(feature) for feature in features]
        if len({row["external_id"] for row in records}) != total:
            message = "Duplicate Groningen source IDs"
            raise ValueError(message)
        return records

    async def collect(self) -> Collection:
        """Verify counts and a full repeated selection, ignoring only volatile IDs."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=45)
            ) as client:
                records = self.parse(await self.request(client))
                repeated = self.parse(await self.request(client))
            if self.claims(records) != self.claims(repeated):
                message = "Groningen source changed during collection"
                raise SourceError(message)
        except (
            aiohttp.ClientError,
            TimeoutError,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            message = "Groningen source retrieval or mapping failed"
            raise SourceError(message) from error
        records.sort(key=lambda row: row["external_id"])
        return Collection(records, len(records), 1, complete=True)

    @staticmethod
    def claims(records: list[dict[str, Any]]) -> list[str]:
        """Compare a multiset of original claims, never derive record identities."""
        return sorted(
            json.dumps(
                {key: value for key, value in row.items() if key != "external_id"},
                sort_keys=True,
                allow_nan=False,
            )
            for row in records
        )

    @staticmethod
    def normalize(feature: dict[str, Any]) -> dict[str, Any]:
        """Keep original polygons and IDs; do not equate a polygon with one bay."""
        identifier, attributes = feature["id"], feature["properties"]
        if not isinstance(attributes, dict) or not isinstance(
            feature["geometry"], dict
        ):
            message = "Invalid Groningen feature objects"
            raise TypeError(message)
        if (
            feature.get("type") != "Feature"
            or not isinstance(identifier, str)
            or not identifier.strip()
            or identifier != identifier.strip()
            or len(identifier) > 255
        ):
            message = "Invalid Groningen source ID"
            raise ValueError(message)
        if (
            attributes.get("TYPE") != "gehandicapten algemeen"
            or attributes.get("ETYPE") != "E06"
        ):
            message = "Invalid Groningen identity or personal/unknown selection"
            raise ValueError(message)
        geometry = Municipality.geometry(feature["geometry"])
        street = attributes.get("STRAATNAAM")
        if street is not None and (not isinstance(street, str) or len(street) > 255):
            message = "Invalid Groningen street"
            raise ValueError(message)
        return {
            "external_id": identifier,
            "geometry": geometry,
            "number": None,
            "street": street,
            "access_category": "general",
            "orientation": ORIENTATIONS.get(attributes.get("SOORT")),
            "source_attributes": attributes.copy(),
            "source_updated_at": None,
        }

    @staticmethod
    def geometry(geometry: dict[str, Any]) -> dict[str, Any]:
        """Validate every original WGS84 ring without deriving a centroid."""
        if geometry.get("type") != "Polygon" or not geometry.get("coordinates"):
            message = "Expected an original Groningen polygon"
            raise ValueError(message)
        for ring in geometry["coordinates"]:
            if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                message = "Invalid Groningen polygon ring"
                raise ValueError(message)
            for point in ring:
                if not isinstance(point, list) or len(point) != 2:
                    message = "Invalid Groningen position"
                    raise ValueError(message)
                for value, bound in zip(point, (180, 90), strict=True):
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                        or not -bound <= value <= bound
                    ):
                        message = "Invalid Groningen WGS84 coordinate"
                        raise ValueError(message)
        return geometry
