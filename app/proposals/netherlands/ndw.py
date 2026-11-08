"""Stream the national NDW current-state selection into a proposal snapshot."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import ijson
import requests
from urllib3.exceptions import HTTPError
from urllib3.util import Retry

from app.records import SourceError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO

CODE = "nl-ndw-e6"
FORMAT = "nipkaart-location-proposals-1"
MAX_BYTES = 64 * 1024 * 1024
MAX_RECORDS = 150_000
MAX_RESPONSE_BYTES = 128 * 1024 * 1024
URL = "https://data.ndw.nu/api/rest/static-road-data/traffic-signs/v4/current-state"
PARAMS = {
    "rvvCode": "E6",
    "status": "PLACED",
    "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
}
SOURCE = {
    "name": "NDW verkeersborden E6",
    "publisher": "Nationaal Dataportaal Wegverkeer",
    "source_url": URL,
    "licence": None,
    "terms_url": "https://docs.ndw.nu/algemeen/data-gebruiksvoorwaarden/",
    "attribution": "NDW Verkeersborden, actueel beeld v4, bewerkt door NIPKaart.",
    "area": {"country": "NL"},
    "bounds": [3.0, 50.5, 7.5, 54.0],
    "expected_interval_hours": 24,
}
UNDER_SIGN_TYPES = frozenset({"VRIJ", "EMIS", "KEN", "RICH", "UIT", "VOOR", "TIJD"})


class UniqueKeys(dict[str, Any]):
    """Reject ambiguous duplicate fields in an upstream feature."""

    def __setitem__(self, key: str, value: Any) -> None:
        """Store the field only if it has not already been supplied."""
        if key in self:
            msg = "NDW feature contains a duplicate JSON field"
            raise SourceError(msg)
        super().__setitem__(key, value)


class BoundedResponse:
    """Enforce a byte ceiling and wall-clock budget while reading the response."""

    def __init__(self, stream: BinaryIO, deadline: float) -> None:
        """Wrap a decoded binary stream."""
        self.stream = stream
        self.deadline = deadline
        self.bytes_read = 0

    def read(self, size: int) -> bytes:
        """Supply bytes to the streaming JSON parser."""
        if monotonic() >= self.deadline:
            msg = "NDW retrieval exceeded its deadline"
            raise SourceError(msg)
        chunk = self.stream.read(size)
        self.bytes_read += len(chunk)
        if self.bytes_read > MAX_RESPONSE_BYTES:
            msg = "NDW response exceeds its byte limit"
            raise SourceError(msg)
        return chunk


def feature_events(
    stream: BinaryIO | BoundedResponse,
) -> Iterator[tuple[str, str, Any]]:
    """Validate the wrapper while passing feature events through to ijson."""
    collection_type = None
    features_array = False
    wrapper_keys: set[str] = set()
    for prefix, event, value in ijson.parse(stream, use_float=True):
        if not prefix and event == "map_key":
            if value in wrapper_keys:
                msg = "NDW feature collection contains a duplicate JSON field"
                raise SourceError(msg)
            wrapper_keys.add(value)
        if prefix == "type" and event == "string":
            collection_type = value
        if prefix == "features" and event == "start_array":
            features_array = True
        yield prefix, event, value
    if collection_type != "FeatureCollection" or not features_array:
        msg = "NDW response is not a single GeoJSON feature collection"
        raise SourceError(msg)


def normalize_feature(feature: dict[str, Any]) -> dict[str, Any]:
    """Keep allowlisted evidence fields without carrying provider free text."""
    properties = feature["properties"]
    if (
        feature["type"] != "Feature"
        or properties["rvvCode"] != PARAMS["rvvCode"]
        or properties["status"] != PARAMS["status"]
    ):
        msg = "NDW returned a feature outside the requested selection"
        raise SourceError(msg)
    geometry = feature["geometry"]
    longitude, latitude = geometry["coordinates"]
    west, south, east, north = SOURCE["bounds"]
    if (
        geometry["type"] != "Point"
        or type(longitude) not in (float, int)
        or type(latitude) not in (float, int)
        or not (west <= longitude <= east and south <= latitude <= north)
    ):
        msg = "NDW feature has an invalid WGS84 point"
        raise SourceError(msg)

    municipality_code = properties.get("countyCode")
    if municipality_code == "":
        municipality_code = None
    if municipality_code is not None and not re.fullmatch(
        r"GM[0-9]{4}", municipality_code
    ):
        msg = "NDW feature has an invalid CBS code"
        raise SourceError(msg)
    last_seen = properties.get("lastSeenOn")
    under_signs = properties.get("textSigns")
    if under_signs is not None and not isinstance(under_signs, list):
        msg = "NDW returned invalid under-sign data"
        raise SourceError(msg)
    under_sign_types = [sign["type"] for sign in (under_signs or [])]
    if any(kind not in UNDER_SIGN_TYPES for kind in under_sign_types):
        msg = "NDW returned an unknown under-sign type"
        raise SourceError(msg)
    return {
        "external_id": str(UUID(feature["id"])),
        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
        "municipality_code": municipality_code,
        "source_last_seen_on": (
            date.fromisoformat(last_seen).isoformat() if last_seen is not None else None
        ),
        "under_sign_types": under_sign_types,
        "personal": "KEN" in under_sign_types,
    }


def write_snapshot(
    stream: BinaryIO | BoundedResponse,
    output: Path,
    retrieved_at: datetime,
    *,
    previous_count: int = 0,
    upstream_total: int | None = None,
) -> int:
    """Commit the delivery only after exhausting and validating the whole response."""
    ids: set[str] = set()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=".parking-", suffix=".tmp", delete=False
        ) as target:
            temporary = Path(target.name)
            target.write(b'{"records":[')
            for feature in ijson.items(
                feature_events(stream), "features.item", map_type=UniqueKeys
            ):
                record = normalize_feature(feature)
                external_id = record["external_id"]
                if external_id in ids or len(ids) >= MAX_RECORDS:
                    msg = "NDW response has duplicate IDs or exceeds its record limit"
                    raise SourceError(msg)
                if ids:
                    target.write(b",")
                ids.add(external_id)
                target.write(encode(record))
                if target.tell() > MAX_BYTES:
                    msg = "NDW delivery exceeds 64 MiB"
                    raise SourceError(msg)

            count = len(ids)
            if not count or (upstream_total is not None and count != upstream_total):
                msg = "NDW response count is empty or disagrees with the API total"
                raise SourceError(msg)
            if count * 5 < previous_count * 4:
                msg = "NDW response count dropped by more than 20%"
                raise SourceError(msg)
            envelope = {
                "format": FORMAT,
                "dataset": CODE,
                "delivery_id": str(uuid4()),
                "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
                "selection": "placed-e6-all",
                "source": SOURCE,
                "complete": True,
                "source_count": count,
                "pages_fetched": 1,
                "upstream_total": upstream_total,
            }
            target.write(b"]," + encode(envelope)[1:] + b"\n")
            if target.tell() > MAX_BYTES:
                msg = "NDW delivery exceeds 64 MiB"
                raise SourceError(msg)
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return count


def encode(value: dict[str, Any]) -> bytes:
    """Encode compact UTF-8 JSON with finite numbers only."""
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode()


def export_snapshot(output: Path, *, previous_count: int = 0) -> int:
    """Fetch one complete national selection, keeping raw sign text out of files."""
    retrieved_at = datetime.now(UTC)
    deadline = monotonic() + 180
    try:
        with requests.Session() as session:
            retry = Retry(
                total=2,
                backoff_factor=0.5,
                status_forcelist=(502, 503, 504),
                respect_retry_after_header=False,
            )
            session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retry))
            with session.get(
                URL, params=PARAMS, stream=True, timeout=(10, 30)
            ) as response:
                return read_snapshot(
                    response, output, retrieved_at, deadline, previous_count
                )
    except (
        requests.RequestException,
        HTTPError,
        ijson.JSONError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
    ) as error:
        msg = "NDW request or response validation failed"
        raise SourceError(msg) from error


def read_snapshot(
    response: requests.Response,
    output: Path,
    retrieved_at: datetime,
    deadline: float,
    previous_count: int,
) -> int:
    """Stream a successful, whole-selection HTTP response into the delivery."""
    if response.status_code != 200:
        msg = "NDW did not return a complete current-state response"
        raise SourceError(msg)
    response.raw.decode_content = True
    total = response.headers.get("X-Total-Count")
    return write_snapshot(
        BoundedResponse(response.raw, deadline),
        output,
        retrieved_at,
        previous_count=previous_count,
        upstream_total=int(total) if total is not None else None,
    )


def last_count(path: Path) -> int:
    """Read the prior acknowledged snapshot count without loading its records."""
    if not path.exists():
        return 0
    with path.open("rb") as stream:
        count = next(ijson.items(stream, "source_count"), None)
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or not 0 < count <= MAX_RECORDS
    ):
        msg = "Last NDW delivery has no valid record count"
        raise SourceError(msg)
    return count
