"""Exercise the adapter boundary with small package objects, without source HTTP."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

from odp_amsterdam.models import ParkingLocations, ParkingSpot

from app.cities.netherlands.amsterdam import Municipality
from app.export import export_amsterdam, write_records


def source_record() -> ParkingSpot:
    """Represent a source claim, including restrictions and a polygon hole."""
    rings = [
        [[4.9, 52.3], [4.91, 52.3], [4.91, 52.31], [4.9, 52.3]],
        [[4.905, 52.301], [4.908, 52.302], [4.907, 52.304], [4.905, 52.301]],
    ]
    return ParkingSpot(
        spot_id="00017460",
        spot_type="E6a",
        spot_description="Gehandicaptenparkeerplaats algemeen",
        street="Teststraat",
        number=2.0,
        orientation="Haaks",
        coordinates=rings[0],
        geometry={"type": "Polygon", "coordinates": rings},
        regimes=[
            {
                "eType": "E6a",
                "eTypeDescription": "Gehandicaptenparkeerplaats algemeen",
                "beginTijd": "09:00:00",
                "dagen": ["ma"],
                "kenteken": "",
            }
        ],
        version_date=date(2026, 9, 1),
    )


class MappingTests(unittest.TestCase):
    """Preserve source meaning and reject scope changes without dropping rows."""

    def test_preserves_source_claims(self) -> None:
        """Full IDs, polygons, restrictions, dates and unknown capacity survive."""
        item = source_record()
        for number in (None, 0, 2.0):
            with self.subTest(number=number):
                record = Municipality().normalize(replace(item, number=number))
                self.assertEqual(record["external_id"], "00017460")
                self.assertEqual(record["geometry"], item.geometry)
                self.assertEqual(record["number"], number)
                self.assertEqual(record["access_category"], "general")
                self.assertEqual(
                    record["source_attributes"],
                    {
                        "regimes": item.regimes,
                        "orientation": "Haaks",
                        "version_date": "2026-09-01",
                    },
                )
                self.assertIsNone(record["source_updated_at"])
        record = Municipality().normalize(replace(item, version_date=None, street=None))
        self.assertIsNone(record["source_attributes"]["version_date"])
        self.assertIsNone(record["street"])

    def test_rejects_invalid_claims(self) -> None:
        """No lossy capacity, guessed identity, out-of-scope regime or bad geometry."""
        item = source_record()
        invalid = [
            replace(item, spot_id=""),
            replace(item, spot_id=" 1"),
            replace(item, number=1.5),
            replace(item, number=-1),
            replace(item, number=True),
            replace(item, number=float("nan")),
            replace(item, spot_type="E6b"),
            replace(item, regimes=[]),
            replace(item, regimes=[*item.regimes, {"eType": "E6b"}]),
            replace(item, regimes=[{**item.regimes[0], "kenteken": "AA-00-AA"}]),
            replace(item, geometry={"type": "Point", "coordinates": [4.9, 52.3]}),
            replace(item, geometry={"type": "Polygon", "coordinates": [[]]}),
            replace(
                item,
                geometry={
                    "type": "Polygon",
                    "coordinates": [
                        [[181, 52], [4, 52], [4, 53], [181, 52]],
                    ],
                },
            ),
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                Municipality().normalize(value)


class WriterTests(unittest.TestCase):
    """Test delivery metadata and failure-safe replacement."""

    def test_delivery_and_failed_replacements(self) -> None:
        """Invalid results, serialization and filesystem failures preserve output."""
        item = source_record()
        result = ParkingLocations(records=[item], total_count=1, pages_fetched=1)
        started = datetime(2026, 9, 14, tzinfo=UTC)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "export.json"
            self.assertEqual(write_records(Municipality(), result, output, started), 1)
            original = output.read_bytes()
            payload = json.loads(original)
            UUID(payload["delivery_id"])
            self.assertEqual(payload["format"], "nipkaart-municipal-pilot-1")
            self.assertEqual(payload["dataset"], "nl-amsterdam-parkeervakken-e6a")
            self.assertEqual(payload["selection"], "e6a-all")
            self.assertEqual(payload["retrieved_at"], "2026-09-14T00:00:00Z")
            self.assertTrue(payload["complete"])
            self.assertEqual(payload["source_count"], len(payload["records"]))
            for invalid in (
                ParkingLocations([], 0, 1),
                ParkingLocations([item], 2, 1),
                ParkingLocations([item, item], 2, 1),
                ParkingLocations([item], 1, 0),
                ParkingLocations([replace(item, number=1.5)], 1, 1),
                ParkingLocations(
                    [
                        replace(
                            item,
                            regimes=[
                                {**item.regimes[0], "aantal": float("nan")},
                            ],
                        )
                    ],
                    1,
                    1,
                ),
            ):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    write_records(Municipality(), invalid, output, started)
                self.assertEqual(output.read_bytes(), original)
            for target, value in (("MAX_BYTES", 1), ("MAX_RECORDS", 0)):
                with (
                    patch(f"app.export.{target}", value),
                    self.assertRaises(ValueError),
                ):
                    write_records(Municipality(), result, output, started)
            for target in ("os.fsync", "Path.replace"):
                with (
                    patch(f"app.export.{target}", side_effect=OSError),
                    self.assertRaises(OSError),
                ):
                    write_records(Municipality(), result, output, started)
                self.assertEqual(output.read_bytes(), original)
                self.assertEqual(list(Path(directory).iterdir()), [output])


class CollectionTests(unittest.IsolatedAsyncioTestCase):
    """Connect package results to the file without duplicating pagination tests."""

    async def test_package_selection(self) -> None:
        """Use the released package for the bounded E6a selection."""
        result = ParkingLocations([source_record()], 1, 1)
        with patch("app.cities.netherlands.amsterdam.ODPAmsterdam") as factory:
            client = factory.return_value.__aenter__.return_value
            client.locations.return_value = result
            self.assertIs(await Municipality().async_get_locations(), result)
            client.locations.assert_awaited_once_with(limit=10001, parking_type="E6a")

    async def test_collection_success_and_failure(self) -> None:
        """Verified package metadata reaches the writer; fetch errors do not."""
        result = ParkingLocations([source_record()], 1, 1)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "export.json"
            with patch(
                "app.export.Municipality.async_get_locations", new_callable=AsyncMock
            ) as fetch:
                fetch.return_value = result
                before = datetime.now(UTC)
                self.assertEqual(await export_amsterdam(output), 1)
                original = output.read_bytes()
                retrieved = datetime.fromisoformat(json.loads(original)["retrieved_at"])
                self.assertLessEqual(before, retrieved)
                self.assertLessEqual(retrieved, datetime.now(UTC))
                fetch.side_effect = TimeoutError("source unavailable")
                with self.assertRaises(TimeoutError):
                    await export_amsterdam(output)
                self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
