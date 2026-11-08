"""Exercise the national proposal delivery boundary without NDW or R2 access."""

# ruff: noqa: PT009, PT027
from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import boto3
import ijson
from botocore.stub import ANY, Stubber

from app.proposals.netherlands import ndw
from app.records import SourceError
from collector import run_once

RETRIEVED_AT = datetime(2026, 11, 8, tzinfo=UTC)


def feature() -> dict:
    """Return a placed sign with typed and unclassified under-sign text."""
    return {
        "type": "Feature",
        "id": str(uuid4()),
        "geometry": {"type": "Point", "coordinates": [4.35, 52.01]},
        "properties": {
            "rvvCode": "E6",
            "status": "PLACED",
            "countyCode": "GM0503",
            "lastSeenOn": "2026-11-07",
            "textSigns": [
                {"type": "KEN", "text": "AB-12-CD"},
                {"type": "VRIJ", "text": "private AB-12-CD"},
            ],
        },
    }


def collection(*features: dict) -> bytes:
    """Encode a provider response with the same wrapper as the live endpoint."""
    return json.dumps({"type": "FeatureCollection", "features": features}).encode()


class NdwTests(unittest.TestCase):
    """Protect completeness, privacy and the private upload namespace."""

    def test_complete_snapshot_preserves_point_evidence_and_omits_text(self) -> None:
        """Personal and unresolved signs still contribute to the national count."""
        personal = feature()
        unresolved = feature()
        unresolved["properties"]["countyCode"] = ""
        unresolved["properties"]["textSigns"] = None
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            count = ndw.write_snapshot(
                io.BytesIO(collection(personal, unresolved)),
                output,
                RETRIEVED_AT,
                upstream_total=2,
            )
            raw = output.read_bytes()

        payload = json.loads(raw)
        self.assertEqual(count, 2)
        self.assertEqual(payload["format"], ndw.FORMAT)
        self.assertEqual(payload["dataset"], ndw.CODE)
        self.assertEqual(payload["source"]["area"], {"country": "NL"})
        self.assertTrue(payload["source"]["terms_url"])
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["source_count"], 2)
        self.assertEqual(payload["upstream_total"], 2)
        self.assertEqual(payload["pages_fetched"], 1)
        self.assertEqual(
            payload["records"][0],
            {
                "external_id": personal["id"],
                "geometry": personal["geometry"],
                "municipality_code": "GM0503",
                "source_last_seen_on": "2026-11-07",
                "under_sign_types": ["KEN", "VRIJ"],
                "personal": True,
            },
        )
        self.assertIsNone(payload["records"][1]["municipality_code"])
        self.assertFalse(payload["records"][1]["personal"])
        self.assertNotIn(b"AB-12-CD", raw)

    def test_invalid_snapshots_preserve_last_good_file(self) -> None:
        """Truncation, duplicates and inconsistent counts never commit an artifact."""
        point = feature()
        wrong_selection = feature()
        wrong_selection["properties"]["status"] = "REMOVED"
        cases = (
            (collection(point)[:-1], 0, None, ijson.JSONError),
            (collection(point, point), 0, None, SourceError),
            (collection(wrong_selection), 0, None, SourceError),
            (collection(), 0, None, SourceError),
            (collection(point), 0, 2, SourceError),
            (collection(point), 2, None, SourceError),
        )
        for raw, previous_count, total, error in cases:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "snapshot.json"
                output.write_bytes(b"last good")
                with self.assertRaises(error):
                    ndw.write_snapshot(
                        io.BytesIO(raw),
                        output,
                        RETRIEVED_AT,
                        previous_count=previous_count,
                        upstream_total=total,
                    )
                self.assertEqual(output.read_bytes(), b"last good")
                self.assertEqual(list(output.parent.iterdir()), [output])

    def test_record_and_byte_limits_reject_the_complete_file(self) -> None:
        """Safety limits reject the delivery instead of truncating the selection."""
        raw = collection(feature(), feature())
        for name, limit in (("MAX_RECORDS", 1), ("MAX_BYTES", 100)):
            with (
                self.subTest(limit=name),
                tempfile.TemporaryDirectory() as directory,
                patch.object(ndw, name, limit),
            ):
                output = Path(directory) / "snapshot.json"
                with self.assertRaises(SourceError):
                    ndw.write_snapshot(io.BytesIO(raw), output, RETRIEVED_AT)
                self.assertFalse(output.exists())

    def test_upload_retry_keeps_same_national_delivery(self) -> None:
        """The NDW CLI route uses the existing immutable PUT and retries exact bytes."""
        client = boto3.client(
            "s3",
            region_name="auto",
            aws_access_key_id="test",
            aws_secret_access_key="test",  # noqa: S106 - in-process SDK stub
        )
        with tempfile.TemporaryDirectory() as directory, Stubber(client) as stub:
            root = Path(directory)
            fixture = root / "fixture.json"
            ndw.write_snapshot(io.BytesIO(collection(feature())), fixture, RETRIEVED_AT)
            raw = fixture.read_bytes()
            key = f"proposals/{ndw.CODE}/{json.loads(raw)['delivery_id']}.json"
            params = {
                "Bucket": "test",
                "Key": key,
                "Body": raw,
                "ContentType": "application/json",
                "ContentMD5": ANY,
                "Metadata": ANY,
                "IfNoneMatch": "*",
            }
            stub.add_client_error(
                "put_object", http_status_code=503, expected_params=params
            )
            stub.add_response("put_object", {}, params)

            def fetch(output: Path, *, previous_count: int) -> int:
                self.assertEqual(previous_count, 0)
                output.write_bytes(raw)
                return 1

            with patch.object(ndw, "export_snapshot", side_effect=fetch) as export:
                with self.assertRaises(client.exceptions.ClientError):
                    run_once(client, "test", root, "ndw")
                self.assertEqual(run_once(client, "test", root, "ndw"), key)
                self.assertEqual(export.call_count, 1)
            self.assertEqual((root / ndw.CODE / "last.json").read_bytes(), raw)
            self.assertEqual(ndw.last_count(root / ndw.CODE / "last.json"), 1)
            stub.assert_no_pending_responses()
