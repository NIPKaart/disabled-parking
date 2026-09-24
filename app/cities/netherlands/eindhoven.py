"""Collect Eindhoven's declared disabled-parking selection for source review."""

from __future__ import annotations

import json
import math
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from app.cities import City
from app.records import Collection, SourceError, capacity

PARKING_TYPE = "Parkeerplaats Gehandicapten"
SOURCE_URL = (
    "https://data.eindhoven.nl/api/explore/v2.1/catalog/datasets/parkeerplaatsen"
)
MAX_RECORDS = 9900
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
PAGE_SIZE = 100


async def request(
    client: ClientSession, path: str = "", params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Read a bounded public response with the session's connection/read deadline."""
    try:
        async with client.get(SOURCE_URL + path, params=params) as response:
            response.raise_for_status()
            body = bytearray()
            async for chunk in response.content.iter_chunked(65536):
                body.extend(chunk)
                if len(body) > MAX_RESPONSE_BYTES:
                    msg = "Eindhoven response exceeds the size limit"
                    raise ValueError(msg)
            result = json.loads(body)
            if not isinstance(result, dict):
                msg = "Expected an Eindhoven response object"
                raise TypeError(msg)
            return result
    except ClientError as error:
        msg = "Eindhoven source request failed"
        raise SourceError(msg) from error


class Municipality(City):
    """Preserve source values without claiming unverified general access."""

    def __init__(self) -> None:
        """Initialize the existing municipality identity."""
        super().__init__(name="Eindhoven", country="Netherlands", geo_code="NL-NB")
        self.cbs_code = "0772"

    async def collect(self) -> Collection:
        """Page in source-ID order and reject changed totals or portal versions."""
        async with ClientSession(timeout=ClientTimeout(total=30, connect=10)) as client:
            before = await request(client)
            version = before["metas"]["default"]["data_processed"]
            if not isinstance(version, str) or not version:
                msg = "Eindhoven portal version is missing"
                raise ValueError(msg)
            records: list[dict[str, Any]] = []
            total = None
            pages = 0
            while total is None or len(records) < total:
                page = await request(
                    client,
                    "/records",
                    {
                        "where": f"type_en_merk='{PARKING_TYPE}'",
                        "order_by": "objectid asc",
                        "limit": PAGE_SIZE,
                        "offset": len(records),
                    },
                )
                count = page["total_count"]
                if (
                    not isinstance(count, int)
                    or isinstance(count, bool)
                    or not 0 < count <= MAX_RECORDS
                    or (total is not None and total != count)
                ):
                    msg = "Invalid or changing Eindhoven source count"
                    raise ValueError(msg)
                total = count
                batch = page["results"]
                if not isinstance(batch, list) or len(batch) != min(
                    PAGE_SIZE, total - len(records)
                ):
                    msg = "Eindhoven returned an incomplete page"
                    raise ValueError(msg)
                records.extend(batch)
                pages += 1
            after = await request(client)
            if after["metas"]["default"]["data_processed"] != version:
                msg = "Eindhoven dataset changed during collection"
                raise ValueError(msg)
        normalized = [self.normalize(record) for record in records]
        ids = [record["external_id"] for record in normalized]
        if len(set(ids)) != total:
            msg = "Eindhoven returned duplicate source IDs"
            raise ValueError(msg)
        return Collection(normalized, total, pages, complete=True)

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
            "source_attributes": {
                "objectid": object_id,
                "type_en_merk": item["type_en_merk"],
            },
            "source_updated_at": None,
        }
