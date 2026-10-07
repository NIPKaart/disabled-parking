"""Verify Arnhem mapping, export preservation and shared collector delivery."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, patch

import boto3
from arnhem import ParkingCollection, ParkingSpot
from arnhem.exceptions import ODPArnhemConnectionError
from botocore.stub import ANY, Stubber

from app.cities.netherlands.arnhem import SELECTION_FILTER, Municipality
from app.export import export_dataset
from app.records import SourceError
from collector import run_once


def source_record(asset_id: int = 1001, sign: str | None = None) -> ParkingSpot:
    """Use package objects with original asset and ArcGIS object identities."""
    return ParkingSpot(
        spot_id=asset_id + 10,
        asset_id=asset_id,
        parking_type="bijzonder",
        street="Willem van Noortstraat",
        traffic_sign="E6a",
        neighborhood=None,
        neighborhood_code=None,
        district=None,
        district_code=None,
        area=None,
        coordinates=[[5.9, 52], [5.91, 52], [5.91, 52.01], [5.9, 52]],
        geometry={
            "type": "Polygon",
            "coordinates": [
                [[5.9, 52], [5.91, 52], [5.91, 52.01], [5.9, 52]],
                [[5.901, 52.001], [5.902, 52.001], [5.902, 52.002], [5.901, 52.001]],
            ],
        },
        source_attributes={
            "ID": asset_id,
            "OBJECTID": asset_id + 10,
            "RVV_SOORT": "E6a",
            "STRAAT": "Willem van Noortstraat",
            "BORD": sign,
            "REGIME": "Mengvorm",
            "SECTIE_ID": 1184,
        },
    )


def collection(*records: ParkingSpot) -> ParkingCollection:
    """Represent a verified package collection."""
    return ParkingCollection(list(records), len(records), 1)


class ArnhemTests(unittest.IsolatedAsyncioTestCase):
    """Exercise source mapping and export without a live source."""

    async def test_complete_selection_preserves_ids_geometry_and_unknown_values(
        self,
    ) -> None:
        """Keep all rings, regime and signage while distinguishing uncertain access."""
        first = source_record()
        signed = source_record(1002, "bezoekers")
        signed.source_attributes["STRAAT"] = None
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.netherlands.arnhem.ODPArnhem") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection = AsyncMock(
                return_value=collection(signed, first)
            )
            output = Path(directory) / "arnhem.json"
            self.assertEqual(await export_dataset("arnhem", output), 2)
            payload = json.loads(output.read_bytes())
        client.parking_collection.assert_awaited_once_with(set_filter=SELECTION_FILTER)
        self.assertEqual(payload["format"], "nipkaart-municipal-2")
        self.assertEqual(payload["dataset"], "nl-arnhem")
        self.assertEqual(payload["selection"], "e6a-all")
        self.assertEqual(payload["source_count"], 2)
        self.assertEqual(payload["source"]["licence"], "CC-BY-4.0")
        self.assertEqual(payload["source"]["area"]["municipality"]["code"], "GM0202")
        row = payload["records"][0]
        self.assertEqual(row["external_id"], "1001")
        self.assertEqual(row["geometry"], first.geometry)
        self.assertEqual(row["source_attributes"], first.source_attributes)
        self.assertEqual(row["access_category"], "general")
        self.assertIsNone(row["number"])
        self.assertIsNone(row["source_updated_at"])
        self.assertIsNone(row["orientation"])
        self.assertEqual(payload["records"][1]["access_category"], "unknown")
        self.assertIsNone(payload["records"][1]["street"])

    async def test_failed_incomplete_or_invalid_collection_keeps_last_export(
        self,
    ) -> None:
        """Keep the last export when the source is empty, duplicate or partial."""
        outside = source_record()
        outside.geometry["coordinates"][0][0] = [4, 52]
        cases = [
            collection(),
            collection(source_record(), source_record()),
            replace(collection(source_record()), complete=False),
            replace(collection(source_record()), total_count=2),
            replace(collection(source_record()), pages_fetched=0),
            collection(outside),
            ODPArnhemConnectionError("Source unavailable"),
            TimeoutError("Deadline exceeded"),
        ]
        for result in cases:
            with (
                self.subTest(result=result),
                tempfile.TemporaryDirectory() as directory,
                patch("app.cities.netherlands.arnhem.ODPArnhem") as factory,
            ):
                client = factory.return_value.__aenter__.return_value
                client.parking_collection = AsyncMock(
                    side_effect=result if isinstance(result, Exception) else None,
                    return_value=result,
                )
                output = Path(directory) / "arnhem.json"
                output.write_bytes(b"last good")
                with self.assertRaises((SourceError, ValueError)):
                    await export_dataset("arnhem", output)
                self.assertEqual(output.read_bytes(), b"last good")

    def test_invalid_identity_category_or_signage_is_rejected(self) -> None:
        """Personal E6b records cannot enter the agreed E6a selection."""
        for field, value in [
            ("ID", 7),
            ("OBJECTID", 7),
            ("RVV_SOORT", "E6b"),
            ("RVV_SOORT", None),
            ("BORD", 7),
            ("STRAAT", 7),
        ]:
            source = source_record()
            source.source_attributes[field] = value
            with self.subTest(field=field), self.assertRaises((ValueError, TypeError)):
                Municipality().normalize(source)
        for value in (0, True, "1001", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Municipality().normalize(replace(source_record(), asset_id=value))
        with self.assertRaises(TypeError):
            Municipality().normalize(replace(source_record(), geometry=None))


class ArnhemCollectorTests(unittest.TestCase):
    """Use the existing immutable transport and isolated dataset state."""

    def test_registered_arnhem_reaches_its_own_r2_prefix(self) -> None:
        """The real adapter goes through the unchanged shared collector pipeline."""
        client = boto3.client(
            "s3",
            region_name="auto",
            aws_access_key_id="test",
            aws_secret_access_key="test",  # noqa: S106 - dummy SDK stub credentials
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.netherlands.arnhem.ODPArnhem") as factory,
            Stubber(client) as stub,
        ):
            source = factory.return_value.__aenter__.return_value
            source.parking_collection = AsyncMock(
                return_value=collection(source_record())
            )
            stub.add_response(
                "put_object",
                {},
                {
                    "Bucket": "test",
                    "Key": ANY,
                    "Body": ANY,
                    "ContentType": "application/json",
                    "ContentMD5": ANY,
                    "Metadata": ANY,
                    "IfNoneMatch": "*",
                },
            )
            key = run_once(client, "test", Path(directory), "arnhem")
            saved = json.loads(
                (Path(directory) / "nl-arnhem" / "last.json").read_bytes()
            )
            self.assertEqual(key, f"municipal/nl-arnhem/{saved['delivery_id']}.json")
            self.assertFalse((Path(directory) / "nl-amsterdam").exists())
            self.assertFalse((Path(directory) / "nl-arnhem" / "pending.json").exists())
            stub.assert_no_pending_responses()
