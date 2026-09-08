"""Write normalized records locally; never connect to core or a database."""
# Copyright (c) 2026 NIPKaart

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from app.cities import City
    from app.records import MunicipalRecord

MAX_RECORDS = 10000
MAX_BYTES = 32 * 1024 * 1024


def _json_default(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(type(value))


def write_records(
    city: City,
    records: Iterable[MunicipalRecord],
    output: Path,
) -> int:
    """Atomically replace a local draft only after every record is validated."""
    header = {
        "format": "municipal-records-draft",
        "source_id": city.source_id,
        "municipality": city.name,
        "country_code": city.geo_code.split("-", 1)[0],
        "region_code": city.geo_code,
        "exported_at": datetime.now(UTC).isoformat(),
        "retrieved_at": None,
        "complete": None,
    }
    seen: set[str] = set()
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=".parking-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(header, ensure_ascii=False)[:-1] + ',"records":[')
            for record in records:
                if record.external_id in seen or len(seen) >= MAX_RECORDS:
                    raise ValueError(record.external_id)
                if seen:
                    stream.write(",")
                seen.add(record.external_id)
                stream.write(
                    json.dumps(
                        asdict(record),
                        ensure_ascii=False,
                        allow_nan=False,
                        default=_json_default,
                    )
                )
                if stream.tell() > MAX_BYTES:
                    raise ValueError(MAX_BYTES)
            stream.write(f'],"record_count":{len(seen)}}}\n')
            if stream.tell() > MAX_BYTES:
                raise ValueError(MAX_BYTES)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return len(seen)
