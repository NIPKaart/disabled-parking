"""Fetch one live source and atomically write the agreed core pilot file."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from app.datasets import DATASETS

if TYPE_CHECKING:
    from collections.abc import Iterator

    from app.datasets import Dataset
    from app.records import Collection

FORMAT = "nipkaart-municipal-2"
MAX_RECORDS = 10000
MAX_BYTES = 32 * 1024 * 1024
FETCH_TIMEOUT = 180


def points(geometry: dict[str, Any]) -> Iterator[list[float]]:
    """Yield every position of a Point, Polygon or MultiPolygon."""
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        yield coordinates
    elif geometry["type"] == "Polygon":
        for ring in coordinates:
            yield from ring
    else:
        for polygon in coordinates:
            for ring in polygon:
                yield from ring


def within(dataset: Dataset, records: list[dict[str, Any]]) -> bool:
    """Every position must lie inside the bounds core approves for the source."""
    west, south, east, north = dataset.description.bounds
    return all(
        west <= longitude <= east and south <= latitude <= north
        for record in records
        for longitude, latitude in points(record["geometry"])
    )


def write_records(
    dataset: Dataset,
    result: Collection,
    output: Path,
    retrieved_at: datetime,
) -> int:
    """Keep the last valid file intact unless the entire delivery is valid."""
    if (
        not result.complete
        or not 0 < result.total_count <= MAX_RECORDS
        or result.pages_fetched < 1
    ):
        msg = "Source delivery is empty, incomplete or exceeds the pilot limit"
        raise ValueError(msg)
    records = result.records
    if (
        len(records) != result.total_count
        or len({record["external_id"] for record in records}) != result.total_count
    ):
        msg = "Source count does not match unique records"
        raise ValueError(msg)
    if retrieved_at.tzinfo is None:
        msg = "Retrieval start must include a timezone"
        raise ValueError(msg)
    if not within(dataset, records):
        msg = "A location lies outside the dataset bounds"
        raise ValueError(msg)
    payload = {
        "format": FORMAT,
        "dataset": dataset.code,
        "delivery_id": str(uuid4()),
        "retrieved_at": retrieved_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "selection": dataset.selection,
        "source": dataset.description.as_dict(),
        "complete": True,
        "source_count": result.total_count,
        "records": records,
    }
    data = (json.dumps(payload, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(data) > MAX_BYTES:
        msg = "Delivery exceeds the 32 MiB pilot limit"
        raise ValueError(msg)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent,
            prefix=".parking-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return len(records)


async def export_dataset(city: str, output: Path) -> int:
    """Bound source collection and write only its verified complete result."""
    dataset = DATASETS[city]
    retrieved_at = datetime.now(UTC)
    async with asyncio.timeout(FETCH_TIMEOUT):
        result = await dataset.source().collect()
    return write_records(dataset, result, output, retrieved_at)
