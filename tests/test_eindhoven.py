"""Check complete Eindhoven collection and the honest review-only mapping."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.cities.netherlands.eindhoven import Municipality
from app.export import export_dataset


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


def metadata(version: str = "2026-09-15T13:42:49+00:00") -> dict:
    """Provide a portal version for detecting changes during retrieval."""
    return {"metas": {"default": {"data_processed": version}}}


class EindhovenTests(unittest.IsolatedAsyncioTestCase):
    """Use the real exporter and mapper with bounded fake source responses."""

    async def test_complete_export_preserves_source_without_claiming_general_access(
        self,
    ) -> None:
        """Every page is fetched, IDs are source IDs and unknown remains unknown."""
        first, second = source_record(), source_record(15627)
        second["aantal"] = None
        second["straat"] = None
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.netherlands.eindhoven.PAGE_SIZE", 1),
            patch(
                "app.cities.netherlands.eindhoven.request",
                new_callable=AsyncMock,
                side_effect=[
                    metadata(),
                    {"total_count": 2, "results": [first]},
                    {"total_count": 2, "results": [second]},
                    metadata(),
                ],
            ) as request,
        ):
            output = Path(directory) / "eindhoven.json"
            self.assertEqual(await export_dataset("eindhoven", output), 2)
            data = json.loads(output.read_bytes())
        self.assertEqual(data["dataset"], "nl-eindhoven")
        self.assertEqual(data["selection"], "gehandicapten-all")
        self.assertEqual(data["source_count"], 2)
        self.assertTrue(data["complete"])
        self.assertEqual(data["records"][0]["external_id"], "15626")
        self.assertEqual(data["records"][0]["geometry"], first["geo_shape"]["geometry"])
        self.assertEqual(data["records"][0]["number"], 1)
        self.assertEqual(data["records"][0]["access_category"], "unknown")
        self.assertIsNone(data["records"][0]["source_updated_at"])
        self.assertIsNone(data["records"][1]["number"])
        self.assertIsNone(data["records"][1]["street"])
        self.assertEqual(request.await_args_list[2].args[2]["offset"], 1)
        self.assertEqual(request.await_args_list[1].args[2]["order_by"], "objectid asc")

    async def test_incomplete_or_changing_source_preserves_last_good_file(self) -> None:
        """No empty, truncated, duplicate or changing selection becomes complete."""
        first = {"total_count": 2, "results": [source_record()]}
        cases = [
            [metadata(), {"total_count": 0, "results": []}],
            [metadata(), {"total_count": True, "results": [source_record()]}],
            [metadata(), {"total_count": 10001, "results": []}],
            [metadata(), first, {"total_count": 3, "results": [source_record(15627)]}],
            [metadata(), first, {"total_count": 2, "results": []}],
            [metadata(), first, first, metadata()],
            [
                metadata(),
                {"total_count": 1, "results": [source_record()]},
                metadata("changed"),
            ],
            [metadata(), TimeoutError("source deadline")],
            [
                metadata(),
                {"total_count": 1, "results": [source_record(), source_record(15627)]},
            ],
        ]
        for responses in cases:
            with (
                self.subTest(responses=responses),
                tempfile.TemporaryDirectory() as directory,
                patch("app.cities.netherlands.eindhoven.PAGE_SIZE", 1),
                patch(
                    "app.cities.netherlands.eindhoven.request", side_effect=responses
                ),
            ):
                output = Path(directory) / "eindhoven.json"
                output.write_bytes(b"last good")
                with self.assertRaises((ValueError, TimeoutError)):
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
