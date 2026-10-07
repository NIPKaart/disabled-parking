"""Check complete Eindhoven collection and the honest review-only mapping."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from eindhoven import Geometry, ParkingCollection, ParkingData, ParkingSpot, ParkingType
from eindhoven.exceptions import ODPEindhovenResultsError

from app.cities.netherlands.eindhoven import Municipality
from app.export import export_dataset
from app.records import SourceError


def source_record(object_id: int = 15626) -> dict:
    """Small source-shaped record, with an actual point rather than a polygon."""
    return {
        "objectid": object_id,
        "straat": "Venbergsemolen",
        "type_en_merk": "Parkeerplaats Gehandicapten",
        "aantal": 1.0,
        "geo_shape": {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [5.48168, 51.44931]},
            "properties": {},
        },
        "geo_point_2d": {"lon": 5.48168, "lat": 51.44931},
    }


def collection(*records: dict) -> ParkingCollection:
    """Make small package results without duplicating source pagination tests."""
    return ParkingCollection(
        [
            ParkingSpot(
                str(row["objectid"]),
                row,
                Geometry(
                    coordinates=row["geo_shape"]["geometry"]["coordinates"],
                    type=row["geo_shape"]["geometry"]["type"],
                ),
                ParkingData(row["type_en_merk"], row["straat"], row["aantal"]),
            )
            for row in records
        ],
        len(records),
        1,
        "2026-09-15T13:42:49+00:00",
    )


class EindhovenTests(unittest.IsolatedAsyncioTestCase):
    """Use the real exporter and mapper with source-package objects."""

    async def test_complete_export_preserves_source_without_claiming_general_access(
        self,
    ) -> None:
        """The package owns retrieval; the collector keeps raw claims and unknowns."""
        first, second = source_record(), source_record(15627)
        second["aantal"] = None
        second["straat"] = None
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.netherlands.eindhoven.ODPEindhoven") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection.return_value = collection(first, second)
            output = Path(directory) / "eindhoven.json"
            self.assertEqual(await export_dataset("eindhoven", output), 2)
            data = json.loads(output.read_bytes())
            client.parking_collection.assert_awaited_once_with(
                parking_type=ParkingType.DISABLED_PARKING, max_records=9900
            )
        self.assertEqual(data["dataset"], "nl-eindhoven")
        self.assertEqual(data["selection"], "gehandicapten-all")
        self.assertEqual(data["source_count"], 2)
        self.assertTrue(data["complete"])
        self.assertEqual(data["records"][0]["external_id"], "15626")
        self.assertEqual(data["records"][0]["geometry"], first["geo_shape"]["geometry"])
        self.assertEqual(data["records"][0]["source_attributes"], first)
        self.assertEqual(data["records"][0]["number"], 1)
        self.assertEqual(data["records"][0]["access_category"], "unknown")
        self.assertIsNone(data["records"][0]["source_updated_at"])
        self.assertIsNone(data["records"][1]["number"])
        self.assertIsNone(data["records"][1]["street"])

    async def test_package_failures_and_invalid_collections_preserve_last_good_file(
        self,
    ) -> None:
        """Source errors and invalid mappings never replace the last valid export."""
        duplicate = collection(source_record(), source_record())
        incomplete = collection(source_record())
        incomplete.complete = False
        mismatched = collection(source_record())
        mismatched.records[0].spot_id = "wrong"
        for result in [
            collection(),
            duplicate,
            incomplete,
            mismatched,
            ODPEindhovenResultsError("incomplete source"),
            TimeoutError("source deadline"),
        ]:
            with (
                self.subTest(result=result),
                tempfile.TemporaryDirectory() as directory,
                patch("app.cities.netherlands.eindhoven.ODPEindhoven") as factory,
            ):
                client = factory.return_value.__aenter__.return_value
                if isinstance(result, Exception):
                    client.parking_collection.side_effect = result
                else:
                    client.parking_collection.return_value = result
                output = Path(directory) / "eindhoven.json"
                output.write_bytes(b"last good")
                with self.assertRaises((SourceError, ValueError)):
                    await export_dataset("eindhoven", output)
                self.assertEqual(output.read_bytes(), b"last good")

    def test_invalid_source_values_are_not_silently_mapped(self) -> None:
        """Reject invented IDs, lossy counts, non-points and scope changes."""
        changes = [
            {"objectid": True},
            {"objectid": "15626"},
            {"objectid": 0},
            {"aantal": -1},
            {"aantal": 1.5},
            {"aantal": True},
            {"type_en_merk": "Parkeerplaats"},
            {"straat": 3},
        ]
        for change in changes:
            with (
                self.subTest(change=change),
                self.assertRaises((ValueError, TypeError)),
            ):
                Municipality().normalize({**source_record(), **change})
        for coordinates in (
            [True, 51],
            [181, 51],
            [5, 91],
            [5],
            ["5", 51],
            [5, float("nan")],
        ):
            item = deepcopy(source_record())
            item["geo_shape"]["geometry"]["coordinates"] = coordinates
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                Municipality().normalize(item)
