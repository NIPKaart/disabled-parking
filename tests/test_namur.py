"""Check Namur's source mapping through the shared export and collector path."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from namur import ParkingCollection, ParkingSpot, ParkingType
from namur.exceptions import ODPNamurConnectionError

from app.cities.belgium.namur import Municipality
from app.export import export_dataset
from app.records import SourceError


def source_spot(spot_id: str = "00040") -> ParkingSpot:
    """Use small package objects, retaining real source-field semantics."""
    return ParkingSpot(
        spot_id=spot_id,
        parking_type="PMR",
        street="Rue Julie Billiart",
        longitude=4.86873,
        latitude=50.46370,
        created_at=datetime(2020, 9, 16, tzinfo=UTC),
        updated_at=datetime(2026, 10, 6, tzinfo=UTC),
        source_attributes={
            "identifiant": spot_id,
            "type_parking": "PMR",
            "rue_nom": "Rue Julie Billiart",
            "geo_shape": {"type": "Point", "coordinates": [4.86873, 50.46370]},
            "date_modif": "2025-02-05",
            "date_creation": "2020-09-16",
            "horaire": "Lundi au Samedi, de 9h à 17h - max. 4h",
            "zone_stationn": "Rouge",
            "largeur": 2.01,
            "longueur": 5.52,
        },
    )


def collection(*records: ParkingSpot) -> ParkingCollection:
    """Represent the package's verified full source selection."""
    return ParkingCollection(list(records), len(records), 1, "2026-10-06T05:03:23Z")


class NamurTests(unittest.IsolatedAsyncioTestCase):
    """Assert preservation and failure behavior, without fetching the live source."""

    async def test_complete_selection_uses_original_ids_geometry_and_source_dates(
        self,
    ) -> None:
        """Keep unknown counts and preserve zone claims without interpretation."""
        first, second = source_spot(), source_spot("1214")
        second.street = None
        second.source_attributes["rue_nom"] = None
        second.source_attributes["date_modif"] = None
        second.source_attributes["horaire"] = "max. 30 minutes"
        second.source_attributes["zone_stationn"] = "Mauve"
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.belgium.namur.ODPNamur") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection = AsyncMock(
                return_value=collection(second, first)
            )
            output = Path(directory) / "namur.json"
            self.assertEqual(await export_dataset("namur", output), 2)
            data = json.loads(output.read_bytes())
        client.parking_collection.assert_awaited_once_with(parking_type=ParkingType.PMR)
        self.assertEqual(data["format"], "nipkaart-municipal-2")
        self.assertEqual(data["dataset"], "be-namur")
        self.assertEqual(data["selection"], "pmr-all")
        self.assertEqual(data["source_count"], 2)
        self.assertTrue(data["complete"])
        self.assertEqual(
            data["source"]["area"],
            {
                "country": "BE",
                "subdivision": "BE-WNA",
                "municipality": {"scheme": "be-ins", "code": "92094", "name": "Namur"},
            },
        )
        self.assertEqual(data["source"]["licence"], "CC-BY-4.0")
        self.assertIn(
            "creativecommons.org/licenses/by/4.0/", data["source"]["attribution"]
        )
        row = data["records"][0]
        self.assertEqual(row["external_id"], "00040")
        self.assertEqual(row["geometry"], first.source_attributes["geo_shape"])
        self.assertEqual(row["source_attributes"], first.source_attributes)
        self.assertEqual(row["source_updated_at"], "2025-02-05")
        self.assertEqual(row["access_category"], "general")
        self.assertIsNone(row["number"])
        self.assertIsNone(row["orientation"])
        self.assertIsNone(data["records"][1]["street"])
        self.assertIsNone(data["records"][1]["source_updated_at"])
        self.assertEqual(
            data["records"][1]["source_attributes"]["horaire"], "max. 30 minutes"
        )

    async def test_failed_incomplete_or_invalid_collection_keeps_previous_export(
        self,
    ) -> None:
        """Reject failed, truncated, duplicate and out-of-area collections."""
        outside = source_spot()
        outside.source_attributes["geo_shape"]["coordinates"] = [4.2, 50.46]
        cases = [
            collection(),
            collection(source_spot(), source_spot()),
            replace(collection(source_spot()), complete=False),
            replace(collection(source_spot()), total_count=2),
            replace(collection(source_spot()), pages_fetched=0),
            collection(outside),
            ODPNamurConnectionError("Source unavailable"),
            TimeoutError("Deadline exceeded"),
        ]
        for result in cases:
            with (
                self.subTest(result=result),
                tempfile.TemporaryDirectory() as directory,
                patch("app.cities.belgium.namur.ODPNamur") as factory,
            ):
                client = factory.return_value.__aenter__.return_value
                client.parking_collection = AsyncMock(
                    side_effect=result if isinstance(result, Exception) else None,
                    return_value=result,
                )
                output = Path(directory) / "namur.json"
                output.write_bytes(b"last good")
                with self.assertRaises((SourceError, ValueError)):
                    await export_dataset("namur", output)
                self.assertEqual(output.read_bytes(), b"last good")

    def test_invalid_ids_scope_geometry_street_or_source_dates_are_rejected(
        self,
    ) -> None:
        """Reject invalid identity, scope, dates and geometry."""
        for changed in [
            {"spot_id": ""},
            {"spot_id": "a" * 256},
            {"spot_id": " 40"},
            {"spot_id": 40},
            {"parking_type": "Réservé"},
            {"street": 3},
            {"street": "a" * 256},
        ]:
            with (
                self.subTest(changed=changed),
                self.assertRaises((ValueError, TypeError)),
            ):
                Municipality().normalize(replace(source_spot(), **changed))
        for changed in [
            {"identifiant": "other"},
            {"type_parking": "Réservé"},
            {"date_modif": "2025-02-30"},
            {"date_modif": "20250205"},
            {"date_modif": "2025-02-05T00:00:00Z"},
            {"date_modif": ""},
            {"date_modif": 20250205},
            {"geo_shape": None},
        ]:
            item = source_spot()
            item.source_attributes.update(changed)
            with (
                self.subTest(changed=changed),
                self.assertRaises((ValueError, TypeError)),
            ):
                Municipality().normalize(item)
        for coordinates in (
            [True, 50],
            [181, 50],
            [4, 91],
            [4],
            ["4", 50],
            [4, float("nan")],
        ):
            item = deepcopy(source_spot())
            item.source_attributes["geo_shape"]["coordinates"] = coordinates
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                Municipality().normalize(item)
        item = source_spot()
        item.source_attributes["geo_shape"]["type"] = "Polygon"
        with self.assertRaises(ValueError):
            Municipality().normalize(item)
