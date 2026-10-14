"""Exercise Köln mapping and failure preservation through existing delivery paths."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from koeln import ParkingCollection, ParkingRecord
from koeln.exceptions import ODPKoelnError

from app.cities.germany.koeln import Municipality
from app.export import export_dataset
from app.records import SourceError
from collector import run_once


def source_record(identity: int = 1, number: int | None = 2) -> ParkingRecord:
    """Use original fields including a literal restriction and address label."""
    return ParkingRecord(
        identity,
        {"type": "Point", "coordinates": [6.95, 50.94]},
        {
            "id": identity,
            "anzahl": number,
            "bezeichnung": "Straße 23",
            "bemerkung": "Mo-Fr 9-17 Uhr, 2 Stunden",
            "nr_stadtbezirk": "1",
        },
    )


class KoelnTests(unittest.IsolatedAsyncioTestCase):
    """Leave HTTP, parser and completeness tests in the reusable package."""

    async def test_export_preserves_original_claims_and_unknowns(self) -> None:
        """General access follows the publisher statement; unknown stays null."""
        items = [source_record(), source_record(2, None), source_record(3, 0)]
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.germany.koeln.StadtKoeln") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection = AsyncMock(
                return_value=ParkingCollection(items, 3, 1, None)
            )
            output = Path(directory) / "koeln.json"
            self.assertEqual(await export_dataset("koeln", output), 3)
            data = json.loads(output.read_bytes())
        client.parking_collection.assert_awaited_once_with()
        self.assertEqual(data["dataset"], "de-koeln")
        self.assertEqual(data["selection"], "general-disabled-all")
        self.assertEqual(
            data["source"]["area"]["municipality"],
            {"scheme": "de-ags", "code": "05315000", "name": "Köln"},
        )
        self.assertEqual(data["source"]["licence"], "DL-DE-ZERO-2.0")
        self.assertEqual([item["number"] for item in data["records"]], [2, None, 0])
        for item, original in zip(data["records"], items, strict=True):
            self.assertEqual(item["external_id"], str(original.id))
            self.assertEqual(item["source_attributes"], original.source_attributes)
            self.assertEqual(item["geometry"], original.geometry)
            self.assertEqual(item["access_category"], "general")
            self.assertIsNone(item["street"])
            self.assertIsNone(item["orientation"])
            self.assertIsNone(item["source_updated_at"])

    def test_invalid_mapping(self) -> None:
        """Reject invalid IDs and lossy or negative capacities."""
        for value in [True, -1, 1.2, "2"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Municipality().normalize(source_record(number=value))
        record = source_record()
        record.source_attributes["id"] = 2
        with self.assertRaises(ValueError):
            Municipality().normalize(record)

    async def test_failure_preserves_last_valid_export(self) -> None:
        """Never replace a good export with failed or incomplete source data."""
        for result in [
            ODPKoelnError("partial source"),
            ParkingCollection([source_record()], 2, 1, None),
            ParkingCollection([source_record()], 1, 1, None, complete=False),
        ]:
            with (
                tempfile.TemporaryDirectory() as directory,
                patch("app.cities.germany.koeln.StadtKoeln") as factory,
            ):
                output = Path(directory) / "last.json"
                output.write_bytes(b"last valid export")
                client = factory.return_value.__aenter__.return_value
                client.parking_collection = (
                    AsyncMock(side_effect=result)
                    if isinstance(result, Exception)
                    else AsyncMock(return_value=result)
                )
                with self.assertRaises((SourceError, ValueError)):
                    await export_dataset("koeln", output)
                self.assertEqual(output.read_bytes(), b"last valid export")

    def test_pending_retry_keeps_dataset_identity(self) -> None:
        """Retry pending bytes without fetching another source delivery."""
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            dataset_state = state / "de-koeln"
            dataset_state.mkdir()
            pending = dataset_state / "pending.json"
            pending.write_bytes(b"pending koeln bytes")
            client = Mock()
            with (
                patch("collector.export_dataset", new_callable=AsyncMock) as fetch,
                patch("collector.upload") as upload,
            ):
                run_once(client, "test", state, "koeln")
            fetch.assert_not_awaited()
            upload.assert_called_once_with(client, "test", pending, "koeln")
            self.assertEqual(
                (dataset_state / "last.json").read_bytes(), b"pending koeln bytes"
            )
