"""Test NIPKaart mapping/output; source parser suites remain upstream."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from hamburg.models import DisabledParking

from app.cities.germany.hamburg import Municipality
from app.export import write_records
from app.records import MunicipalRecord, capacity

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/hamburg.json"


def source_record() -> DisabledParking:
    """Build a small package object for our mapping tests."""
    return DisabledParking(
        spot_id="00017460",
        street=" Teststraat 1 ",
        limitation="max. 2h",
        number=2,
        longitude=9.9,
        latitude=53.5,
    )


class MappingTests(unittest.TestCase):
    """Keep identity, unknown values and restrictions meaningful."""

    def test_mapping_preserves_source_meaning(self) -> None:
        """Full IDs and restrictions survive mapping; source dates are not invented."""
        city = Municipality()
        record = city.normalize(source_record())
        self.assertEqual(record.external_id, "00017460")
        self.assertEqual(record.street, "Teststraat 1")
        self.assertEqual((record.latitude, record.longitude), (53.5, 9.9))
        self.assertEqual(record.number, 2)
        self.assertEqual(record.source_attributes, {"limitation": "max. 2h"})
        self.assertIsNone(record.source_updated_at)
        for number in (None, 0):
            with self.subTest(number=number):
                item = replace(source_record(), number=number, street=None)
                record = city.normalize(item)
                self.assertEqual(record.number, number)
                self.assertIsNone(record.street)

    def test_invalid_capacity_and_coordinates(self) -> None:
        """Invalid counts/coordinates cannot enter a delivery."""
        for value in (-1, 1.5, "NaN", "Infinity", True):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                capacity(value)
        for latitude, longitude in ((91, 5), (52, 181), (float("nan"), 5)):
            with self.subTest(latitude=latitude), self.assertRaises(ValueError):
                MunicipalRecord(
                    external_id="1", latitude=latitude, longitude=longitude, number=None
                )


class WriterTests(unittest.TestCase):
    """Exercise success and data-loss boundaries with small normalized objects."""

    def test_success_and_failure_preserve_existing_output(self) -> None:
        """Unknown completeness stays explicit and failures preserve the last file."""
        city = Municipality()
        record = city.normalize(source_record())
        records = [record, replace(record, external_id="second")]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "export.json"
            self.assertEqual(write_records(city, records, output), 2)
            original = output.read_bytes()
            payload = json.loads(original)
            self.assertEqual(payload["record_count"], 2)
            self.assertIsNone(payload["complete"])
            self.assertIsNone(payload["retrieved_at"])
            self.assertEqual(payload["source_id"], "DE-HH-040")
            for field in ("visibility", "legacy_id", "country_id", "province_id"):
                self.assertNotIn(field, payload["records"][0])
            with self.assertRaises(ValueError):
                write_records(city, [record, record], output)
            with patch("app.export.MAX_RECORDS", 1), self.assertRaises(ValueError):
                write_records(city, records, output)
            with patch("app.export.MAX_BYTES", 1), self.assertRaises(ValueError):
                write_records(city, records, output)
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_failed_mapping_leaves_previous_file(self) -> None:
        """A producer failing midway must not publish a partial result."""
        city = Municipality()
        items = [source_record(), replace(source_record(), longitude=181)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "export.json"
            output.write_text("previous", encoding="utf-8")
            with self.assertRaises(ValueError):
                write_records(city, (city.normalize(item) for item in items), output)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous")
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_cli_package_boundary_without_network(self) -> None:
        """One tiny upstream sample verifies installed parser → adapter → file."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "export.json"
            code = (
                "import runpy,socket; from unittest.mock import patch; "
                "guard=patch.object(socket.socket,'connect',"
                "side_effect=AssertionError('network')); guard.start(); "
                "runpy.run_path('export.py',run_name='__main__')"
            )
            result = subprocess.run(  # noqa: S603
                [
                    sys.executable,
                    "-c",
                    code,
                    "--city",
                    "hamburg",
                    "--input",
                    str(FIXTURE),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["record_count"], 1)
            self.assertEqual(payload["records"][0]["external_id"], "7460")
            self.assertIn("completeness has not been verified", result.stdout)

    def test_cli_failure_keeps_existing_file(self) -> None:
        """Unsupported examples and malformed responses cannot replace a file."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            output = Path(directory) / "output.json"
            source.write_text("{}", encoding="utf-8")
            output.write_text("previous", encoding="utf-8")
            for city in ("hamburg", "amsterdam"):
                with self.subTest(city=city):
                    result = subprocess.run(  # noqa: S603
                        [
                            sys.executable,
                            "export.py",
                            "--city",
                            city,
                            "--input",
                            str(source),
                            "--output",
                            str(output),
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(output.read_text(encoding="utf-8"), "previous")


if __name__ == "__main__":
    unittest.main()
