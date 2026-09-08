"""Export a captured municipal response through the existing package and adapter."""
# Copyright (c) 2026 NIPKaart

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.cities.provider import CityProvider
from app.export import MAX_BYTES, write_records


def read_input(path: Path) -> dict:
    """Bound the captured response before decoding it."""
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(MAX_BYTES)
    return json.loads(data)


def main() -> None:
    """Produce a local draft without fetching data or opening a database."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", required=True)
    parser.add_argument(
        "--input", required=True, type=Path, help="Captured JSON response"
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        city = CityProvider().provide_city(args.city.lower())
        payload = read_input(args.input)
        items = city.source_items(payload)
        count = write_records(
            city, (city.normalize(item) for item in items), args.output
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        RecursionError,
    ) as error:
        parser.exit(1, f"Export failed: {error}\n")
    print(f"Exported {count} records; source completeness has not been verified.")


if __name__ == "__main__":
    main()
