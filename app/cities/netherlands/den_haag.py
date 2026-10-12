"""Collect the original general-parking WFS used by Den Haag's public map."""

from __future__ import annotations

import math
from typing import Any

import aiohttp

from app.cities import City
from app.records import Collection, SourceError, capacity

SOURCE_URL = "https://denhaag-gs.gisib.nl:8443/geoserver/DenHaag/wfs"
FEATURE_TYPE = "DenHaag:Parkeerplek_gehandicapten_DPZ_Teamwebsites_centroide"
PAGE_SIZE = 100
MAX_RECORDS = 10000
ORIENTATIONS = {"File": "parallel", "Haaks": "perpendicular", "Visgraat": "angle"}


class Municipality(City):
    """Keep municipal IDs and original claims; core owns source approval."""

    def __init__(self) -> None:
        """Initialize the existing municipality identity."""
        super().__init__(name="Den Haag", country="Netherlands", geo_code="NL-ZH")
        self.cbs_code = "0518"

    async def request(
        self, client: aiohttp.ClientSession, offset: int
    ) -> dict[str, Any]:
        """Request WGS84 GeoJSON with deterministic original-ID ordering."""
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": FEATURE_TYPE,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "sortBy": "ID",
            "count": PAGE_SIZE,
            "startIndex": offset,
        }
        async with client.get(SOURCE_URL, params=params) as response:
            response.raise_for_status()
            result = await response.json()
        if not isinstance(result, dict) or result.get("type") != "FeatureCollection":
            message = "Expected a Den Haag WFS FeatureCollection"
            raise ValueError(message)
        return result

    @staticmethod
    def page(result: dict[str, Any], expected: int | None) -> tuple[int, list]:
        """Reject changed totals, malformed pages and unexpected coordinate systems."""
        total, features = result["numberMatched"], result["features"]
        if (
            isinstance(total, bool)
            or not isinstance(total, int)
            or not 0 < total <= MAX_RECORDS
            or (expected is not None and total != expected)
        ):
            message = "Invalid or changed Den Haag WFS count"
            raise ValueError(message)
        returned = result["numberReturned"]
        if (
            not isinstance(features, list)
            or isinstance(returned, bool)
            or not isinstance(returned, int)
            or returned != len(features)
            or result["crs"]["properties"]["name"] != "urn:ogc:def:crs:EPSG::4326"
        ):
            message = "Invalid or changed Den Haag WFS page"
            raise ValueError(message)
        return total, features

    async def collect(self) -> Collection:
        """Check every page, unique municipal IDs and a repeated first page."""
        try:
            return await self.retrieve()
        except (
            aiohttp.ClientError,
            TimeoutError,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            message = "Den Haag source retrieval or mapping failed"
            raise SourceError(message) from error

    async def retrieve(self) -> Collection:
        """Retrieve all pages without returning partial collections."""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as client:
            result = await self.request(client, 0)
            total, page = self.page(result, None)
            records = []
            pages = 0
            while True:
                if len(page) != min(PAGE_SIZE, total - len(records)):
                    message = "Truncated or oversized Den Haag WFS page"
                    raise ValueError(message)
                records.extend(self.normalize(feature) for feature in page)
                pages += 1
                if len(records) == total:
                    break
                result = await self.request(client, len(records))
                _, page = self.page(result, total)
            if len({record["external_id"] for record in records}) != total:
                message = "Duplicate Den Haag municipal IDs"
                raise ValueError(message)
            check = await self.request(client, 0)
            _, repeated = self.page(check, total)
            if [self.normalize(feature) for feature in repeated] != records[:PAGE_SIZE]:
                message = "Den Haag selection changed during retrieval"
                raise ValueError(message)
        records.sort(key=lambda record: record["external_id"])
        return Collection(records, total, pages, complete=True)

    def normalize(self, feature: dict[str, Any]) -> dict[str, Any]:
        """Use source Points and IDs without interpreting dates as updates."""
        attributes = feature["properties"]
        identifier = attributes["ID"]
        if (
            feature.get("type") != "Feature"
            or isinstance(identifier, bool)
            or not isinstance(identifier, int)
            or identifier <= 0
        ):
            message = "Invalid Den Haag municipal ID"
            raise ValueError(message)
        purpose = attributes["GEBRUIKSDOEL"]
        if not isinstance(purpose, str):
            message = "Missing Den Haag access claim"
            raise TypeError(message)
        purposes = {value.strip() for value in purpose.split(",")}
        if (
            "Gehandicapte algemeen" not in purposes
            or "Gehandicapte op kenteken" in purposes
        ):
            message = "Unexpected Den Haag selection or personal reservation"
            raise ValueError(message)
        geometry = feature["geometry"]
        point = geometry["coordinates"]
        if (
            geometry.get("type") != "Point"
            or not isinstance(point, list)
            or len(point) != 2
        ):
            message = "Expected a Den Haag WGS84 Point"
            raise ValueError(message)
        for value, bound in zip(point, (180, 90), strict=True):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not -bound <= value <= bound
            ):
                message = "Invalid Den Haag WGS84 coordinate"
                raise ValueError(message)
        return {
            "external_id": str(identifier),
            "geometry": geometry,
            "number": capacity(attributes["CAPACITEIT"]),
            "street": None,
            "access_category": (
                "general"
                if purposes <= {"Gehandicapte algemeen", "Parkeergelegenheid"}
                else "unknown"
            ),
            "orientation": ORIENTATIONS.get(attributes["ORIENTATIE"]),
            "source_attributes": attributes.copy(),
            "source_updated_at": None,
        }
