"""Verify Groningen selection, volatile IDs and failed-export preservation."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.cities.netherlands.groningen import Municipality
from app.export import export_dataset
from app.records import SourceError


def feature(identifier: str = "Parkeervakken.fid-first") -> dict:
    """Small WFS-shaped source claim, including its original polygon."""
    return {
        "type": "Feature",
        "id": identifier,
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[6.56, 53.21], [6.5601, 53.21], [6.5601, 53.2101], [6.56, 53.21]],
            ],
        },
        "properties": {
            "TYPE": "gehandicapten algemeen",
            "ETYPE": "E06",
            "SOORT": "langsparkeren",
            "STRAATNAAM": "Teststraat",
            "VENSTERTIJD": None,
            "WIT_KRUIS": "ja",
        },
    }


def response(*features: dict) -> dict:
    """Complete source envelope rather than a silently truncated list."""
    return {
        "type": "FeatureCollection",
        "numberMatched": len(features),
        "numberReturned": len(features),
        "features": list(features),
        "crs": {"properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
    }


class GroningenTests(unittest.IsolatedAsyncioTestCase):
    """Changing feature IDs alone must not reject otherwise unchanged claims."""

    async def test_complete_export_preserves_original_id_and_unknown_capacity(
        self,
    ) -> None:
        """The repeated request may change IDs; it may not change source claims."""
        first = feature()
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(Municipality, "request", new_callable=AsyncMock) as request,
        ):
            request.side_effect = [response(first), response(feature("new-id"))]
            output = Path(directory) / "groningen.json"
            self.assertEqual(await export_dataset("groningen", output), 1)
            payload = json.loads(output.read_bytes())
        row = payload["records"][0]
        self.assertEqual(row["external_id"], first["id"])
        self.assertEqual(row["geometry"], first["geometry"])
        self.assertEqual(row["source_attributes"], first["properties"])
        self.assertEqual(row["access_category"], "general")
        self.assertEqual(row["orientation"], "parallel")
        self.assertIsNone(row["number"])
        self.assertIsNone(row["source_updated_at"])
        self.assertEqual(payload["source"]["licence"], "CC-BY-4.0")
        self.assertEqual(payload["source_count"], 1)
        self.assertEqual(request.await_count, 2)

    async def test_bad_or_changed_selection_preserves_previous_export(self) -> None:
        """No partial, duplicate, changed or personally reserved snapshot escapes."""
        truncated = response(feature())
        truncated["numberMatched"] = 2
        personal = feature()
        personal["properties"]["TYPE"] = "gehandicapten kenteken"
        missing = feature()
        missing["id"] = None
        changed = feature("new-id")
        changed["properties"]["VENSTERTIJD"] = "ma-vr"
        bad_coordinate = feature()
        bad_coordinate["geometry"]["coordinates"][0][1][0] = True
        for responses in (
            [truncated],
            [response()],
            [response(feature(), feature())],
            [response(personal)],
            [response(missing)],
            [response(bad_coordinate)],
            [response(feature()), response(changed)],
            [response(feature()), TimeoutError("verification failed")],
        ):
            with (
                self.subTest(responses=responses),
                tempfile.TemporaryDirectory() as directory,
                patch.object(
                    Municipality, "request", new_callable=AsyncMock
                ) as request,
            ):
                request.side_effect = deepcopy(responses)
                output = Path(directory) / "groningen.json"
                output.write_bytes(b"last valid export")
                with self.assertRaises(SourceError):
                    await export_dataset("groningen", output)
                self.assertEqual(output.read_bytes(), b"last valid export")
