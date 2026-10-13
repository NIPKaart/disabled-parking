"""Exercise the identified Antwerpen selection through the shared exporter."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from antwerpen import ParkingCollection, ParkingRecord
from antwerpen.exceptions import ODPAntwerpenConnectionError

from app.cities.belgium.antwerpen import SELECTION_FILTER, Municipality
from app.export import export_dataset
from app.records import SourceError
from collector import run_once


def source_record(identity: str = "GIS_10198") -> ParkingRecord:
    """Use small original polygons and claims, including a time restriction."""
    return ParkingRecord(
        identity,
        {
            "type": "Polygon",
            "coordinates": [[[4.4, 51.2], [4.401, 51.2], [4.4, 51.201], [4.4, 51.2]]],
        },
        {
            "GISID": identity,
            "OBJECTID": 1,
            "STATUS": "actief",
            "Capaciteit": 1,
            "Orientatie": "Langs",
            "toegang": "Beperkt",
            "Venstertijd": "ja",
            "VENSTERTIJD_BESCHR": "ma-vr 09:00-17:00",
            "EBDD": 1691625600000,
            "Opnamedatum": None,
        },
    )


class AntwerpenTests(unittest.IsolatedAsyncioTestCase):
    """Keep mapping and delivery failure coverage separate from upstream HTTP tests."""

    async def test_export_retains_geometry_unknowns_and_source_claims(self) -> None:
        """Never infer general access or a modification date from these claims."""
        first, second, third = (
            source_record(),
            source_record("GIS_2"),
            source_record("GIS_3"),
        )
        second.source_attributes["Capaciteit"] = None
        second.source_attributes["Orientatie"] = None
        third.source_attributes["Capaciteit"] = 0
        first.geometry["coordinates"].append(
            [[4.4001, 51.2001], [4.4001, 51.2002], [4.4002, 51.2001], [4.4001, 51.2001]]
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.belgium.antwerpen.ODPAntwerpen") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection = AsyncMock(
                return_value=ParkingCollection([third, second, first], 3, 2, None)
            )
            output = Path(directory) / "antwerpen.json"
            self.assertEqual(await export_dataset("antwerpen", output), 3)
            data = json.loads(output.read_bytes())
        client.parking_collection.assert_awaited_once_with(set_filter=SELECTION_FILTER)
        self.assertEqual(data["dataset"], "be-antwerpen")
        self.assertEqual(data["selection"], "identified-disabled-all")
        self.assertEqual(data["source_count"], 3)
        self.assertEqual(
            data["source"]["area"]["municipality"],
            {"scheme": "be-ins", "code": "11002", "name": "Antwerpen"},
        )
        self.assertIsNone(data["source"]["licence"])
        self.assertIn("bron stad Antwerpen", data["source"]["attribution"])
        records = data["records"]
        self.assertEqual(records[0]["external_id"], first.gis_id)
        self.assertEqual(records[0]["geometry"], first.geometry)
        self.assertEqual(records[0]["source_attributes"], first.source_attributes)
        self.assertEqual(records[0]["orientation"], "parallel")
        self.assertEqual([record["number"] for record in records], [1, None, 0])
        for record in records:
            self.assertEqual(record["access_category"], "unknown")
            self.assertIsNone(record["street"])
            self.assertIsNone(record["source_updated_at"])

    def test_invalid_mapping(self) -> None:
        """Reject malformed source identity, capacity, status and coordinates."""
        original = source_record()
        for name, value in [
            ("GISID", None),
            ("GISID", "other"),
            ("Capaciteit", -1),
            ("Capaciteit", True),
            ("Capaciteit", "1"),
            ("STATUS", "vervallen"),
        ]:
            with self.subTest(name=name, value=value):
                record = deepcopy(original)
                record.source_attributes[name] = value
                with self.assertRaises(ValueError):
                    Municipality().normalize(record)
        for geometry in [
            None,
            {"type": "Point", "coordinates": [4.4, 51.2]},
            {"type": "Polygon", "coordinates": []},
            {"type": "Polygon", "coordinates": [[[4.4, 51.2]]]},
        ]:
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                Municipality().normalize(
                    ParkingRecord(original.gis_id, geometry, original.source_attributes)
                )

    def test_orientations_and_uncertain_access(self) -> None:
        """Translate known orientation claims without inventing access permissions."""
        for source, expected in [
            ("Langs", "parallel"),
            ("Dwars", "perpendicular"),
            ("Schuin", "angle"),
            (None, None),
            ("other", None),
        ]:
            with self.subTest(orientation=source):
                record = source_record()
                record.source_attributes["Orientatie"] = source
                record.source_attributes["toegang"] = None
                normalized = Municipality().normalize(record)
                self.assertEqual(normalized["orientation"], expected)
                self.assertEqual(normalized["access_category"], "unknown")
        for value in [True, float("nan"), float("inf"), 181, "4.4"]:
            with self.subTest(coordinate=value):
                record = source_record()
                record.geometry["coordinates"][0][0][0] = value
                record.geometry["coordinates"][0][-1][0] = value
                with self.assertRaises(ValueError):
                    Municipality().normalize(record)

    async def test_failures_preserve_previous_export(self) -> None:
        """Retrieval, completeness, identity and bounds errors replace no file."""
        outside = source_record()
        outside.geometry["coordinates"][0][0] = [5, 51.2]
        outside.geometry["coordinates"][0][-1] = [5, 51.2]
        failures = [
            ODPAntwerpenConnectionError("offline"),
            ParkingCollection([source_record()], 1, 1, None, complete=False),
            ParkingCollection([source_record()], 2, 1, None),
            ParkingCollection([source_record(), source_record()], 2, 1, None),
            ParkingCollection([outside], 1, 1, None),
            ParkingCollection([], 0, 2, None),
        ]
        for failure in failures:
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as directory,
                patch("app.cities.belgium.antwerpen.ODPAntwerpen") as factory,
            ):
                client = factory.return_value.__aenter__.return_value
                client.parking_collection = (
                    AsyncMock(side_effect=failure)
                    if isinstance(failure, Exception)
                    else AsyncMock(return_value=failure)
                )
                output = Path(directory) / "antwerpen.json"
                output.write_bytes(b"previous valid export")
                with self.assertRaises((SourceError, ValueError)):
                    await export_dataset("antwerpen", output)
                self.assertEqual(output.read_bytes(), b"previous valid export")


class AntwerpenCollectorTests(unittest.TestCase):
    """Use the shared immutable transport and isolated retry state."""

    def test_delivery_uses_own_prefix_and_retries_identical_bytes(self) -> None:
        """A failed upload must not refetch or replace a pending Antwerpen delivery."""
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.cities.belgium.antwerpen.ODPAntwerpen") as factory,
        ):
            client = factory.return_value.__aenter__.return_value
            client.parking_collection = AsyncMock(
                return_value=ParkingCollection([source_record()], 1, 2, None)
            )
            bucket = Mock()
            bucket.put_object.side_effect = OSError("unavailable")
            with self.assertRaises(OSError):
                run_once(bucket, "test", Path(directory), "antwerpen")
            pending = Path(directory) / "be-antwerpen" / "pending.json"
            original = pending.read_bytes()
            bucket.put_object.side_effect = None
            key = run_once(bucket, "test", Path(directory), "antwerpen")
            self.assertTrue(key.startswith("municipal/be-antwerpen/"))
            self.assertEqual(bucket.put_object.call_args.kwargs["Body"], original)
            self.assertEqual(bucket.put_object.call_args.kwargs["IfNoneMatch"], "*")
            self.assertFalse(pending.exists())
            self.assertEqual((pending.parent / "last.json").read_bytes(), original)
            client.parking_collection.assert_awaited_once()
