"""Check Stockholm mapping, safe failures and the shared delivery path."""
# ruff: noqa: PT009, PT027

import json
import os
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from odp_stockholm import ODPStockholmError, ParkingCollection, ParkingSpot, ParkingType

import collector
from app.cities.sweden.stockholm import Municipality
from app.export import export_dataset
from app.records import SourceError


def source_spot(fid: int = 1) -> ParkingSpot:
    """Represent source fields, including the misleading extent number."""
    geometry = {"type": "LineString", "coordinates": [[18.08, 59.30], [18.09, 59.31]]}
    source = {
        "id": f"LTFR_P_RORELSEHINDRADE.{fid}",
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "FID": fid,
            "EXTENT_NO": 4475,
            "VF_PLATSER": 2,
            "STREET_NAME": "Tomträttsvägen",
            "VALID_FROM": "2020-03-28T23:00:00Z",
            "VALID_TO": None,
            "CITATION": "0180 2020-01573",
            "VF_PLATS_TYP": "Reserverad p-plats rörelsehindrad",
        },
    }
    return ParkingSpot(source["id"], geometry, "Tomträttsvägen", source)


def collection(*records: ParkingSpot) -> ParkingCollection:
    """Represent a package-verified complete selection."""
    return ParkingCollection(list(records), len(records), 1, None)


class StockholmTests(unittest.IsolatedAsyncioTestCase):
    """Exercise product claims and atomic export with the real shared writer."""

    async def test_export_preserves_lines_identity_and_unknown_values(self) -> None:
        """Do not convert regulations into invented bay counts or survey dates."""
        first, second = source_spot(), source_spot(2)
        second.geometry["type"] = "MultiLineString"
        second.geometry["coordinates"] = [second.geometry["coordinates"]]
        second.street = None
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"STOCKHOLM_API_KEY": "fake"}),
            patch("app.cities.sweden.stockholm.ParkingStockholm") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection = AsyncMock(
                return_value=collection(second, first)
            )
            output = Path(directory) / "stockholm.json"
            self.assertEqual(await export_dataset("stockholm", output), 2)
            data = json.loads(output.read_bytes())
        client.parking_collection.assert_awaited_once_with(
            parking_type=ParkingType.DISABLED
        )
        self.assertEqual(data["format"], "nipkaart-municipal-2")
        self.assertEqual(data["dataset"], "se-stockholm")
        self.assertEqual(data["selection"], "prorelsehindrad-all")
        self.assertEqual(
            data["source"]["area"]["municipality"],
            {"scheme": "se-scb", "code": "0180", "name": "Stockholm"},
        )
        self.assertIsNone(data["source"]["licence"])
        self.assertEqual(data["records"][0]["external_id"], first.id)
        self.assertEqual(data["records"][0]["geometry"], first.geometry)
        self.assertEqual(
            data["records"][0]["source_attributes"], first.source_attributes
        )
        self.assertEqual(data["records"][0]["access_category"], "unknown")
        self.assertIsNone(data["records"][0]["number"])
        self.assertIsNone(data["records"][0]["source_updated_at"])
        self.assertIsNone(data["records"][0]["orientation"])
        self.assertNotIn("fake", json.dumps(data))

    async def test_failures_never_replace_the_last_export(self) -> None:
        """Reject partial, duplicate and outside data as well as source failures."""
        outside = source_spot()
        outside.geometry["coordinates"][1] = [18.5, 59.3]
        multiline = source_spot()
        multiline.geometry["type"] = "MultiLineString"
        multiline.geometry["coordinates"] = [
            multiline.geometry["coordinates"],
            [[18.1, 59.3], [18.5, 59.3]],
        ]
        for result in [
            collection(),
            collection(source_spot(), source_spot()),
            replace(collection(source_spot()), complete=False),
            replace(collection(source_spot()), total_count=2),
            collection(outside),
            collection(multiline),
            ODPStockholmError("bad response"),
            TimeoutError(),
        ]:
            with (
                self.subTest(result=result),
                tempfile.TemporaryDirectory() as directory,
                patch.dict(os.environ, {"STOCKHOLM_API_KEY": "fake"}),
                patch("app.cities.sweden.stockholm.ParkingStockholm") as factory,
            ):
                client = factory.return_value.__aenter__.return_value
                client.parking_collection = AsyncMock(
                    side_effect=result if isinstance(result, Exception) else None,
                    return_value=result,
                )
                output = Path(directory) / "stockholm.json"
                output.write_bytes(b"last good")
                with self.assertRaises((SourceError, ValueError)):
                    await export_dataset("stockholm", output)
                self.assertEqual(output.read_bytes(), b"last good")

    async def test_missing_key_fails_before_request(self) -> None:
        """An unconfigured source must fail rather than become an empty delivery."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("app.cities.sweden.stockholm.ParkingStockholm") as factory,
            self.assertRaises(SourceError),
        ):
            await Municipality().collect()
        factory.assert_not_called()

    def test_invalid_source_claims_are_rejected(self) -> None:
        """Reject lossy identity and malformed coordinate types."""
        for coordinates in [
            [[True, 59.3], [18, 59.4]],
            [[18, 59.3]],
            [[181, 59.3], [18, 59.4]],
            [[18, float("nan")], [18, 59.4]],
            [[18, 59.3, 1], [18, 59.4, 1]],
        ]:
            item = deepcopy(source_spot())
            item.geometry["coordinates"] = coordinates
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                Municipality().normalize(item)
        item = source_spot()
        item.source_attributes["properties"]["FID"] = True
        with self.assertRaises(ValueError):
            Municipality().normalize(item)
        with self.assertRaises(ValueError):
            Municipality().normalize(replace(source_spot(), id="wrong"))
        item = source_spot()
        item.source_attributes["properties"]["VF_PLATS_TYP"] = "other parking"
        with self.assertRaises(ValueError):
            Municipality().normalize(item)


class StockholmCollectorTests(unittest.TestCase):
    """Route Stockholm through the existing private delivery and pending state."""

    def test_delivery_uses_own_prefix_and_pending_retry(self) -> None:
        """Retry the same bytes and identity without collecting a replacement."""
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"STOCKHOLM_API_KEY": "fake"}),
            patch("app.cities.sweden.stockholm.ParkingStockholm") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection = AsyncMock(
                return_value=collection(source_spot())
            )
            bucket = Mock()
            bucket.put_object.side_effect = OSError("unavailable")
            with self.assertRaises(OSError):
                collector.run_once(bucket, "test", Path(directory), "stockholm")
            pending = Path(directory) / "se-stockholm" / "pending.json"
            original = pending.read_bytes()
            bucket.put_object.side_effect = None
            key = collector.run_once(bucket, "test", Path(directory), "stockholm")
            self.assertTrue(key.startswith("municipal/se-stockholm/"))
            self.assertEqual(bucket.put_object.call_args.kwargs["Body"], original)
            self.assertFalse(pending.exists())
            self.assertEqual((pending.parent / "last.json").read_bytes(), original)
            client.parking_collection.assert_awaited_once()
