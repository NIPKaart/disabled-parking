"""Export Amsterdam general accessible parking to a local file for core review."""

import argparse
import asyncio
from pathlib import Path

from odp_amsterdam.exceptions import ODPAmsterdamError

from app.export import export_amsterdam


def main() -> None:
    """Fetch one complete selection; never publish or connect to core."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", required=True, choices=["amsterdam"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = asyncio.run(export_amsterdam(args.output))
    except (ODPAmsterdamError, OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"Export failed: {error}\n")
    print(f"Exported {count} records; complete source selection ready for core review.")


if __name__ == "__main__":
    main()
