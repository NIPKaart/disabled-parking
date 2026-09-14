"""Test recovery using real SDK request validation without source or bucket access."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import boto3
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

from collector import DATASET, run_once, upload


class CollectorTests(unittest.TestCase):
    """Keep the exact delivery on failures and refuse identity conflicts."""

    def setUp(self) -> None:
        """Use dummy credentials with botocore's in-process stub."""
        self.client = boto3.client(
            "s3",
            region_name="auto",
            aws_access_key_id="test",
            aws_secret_access_key="test",  # noqa: S106 - dummy SDK stub credentials
        )
        self.data = (
            json.dumps(
                {
                    "dataset": DATASET,
                    "delivery_id": str(uuid4()),
                    "records": [],
                }
            )
            + "\n"
        ).encode()
        self.key = f"municipal/{DATASET}/{json.loads(self.data)['delivery_id']}.json"
        self.parameters = {
            "Bucket": "test",
            "Key": self.key,
            "Body": self.data,
            "ContentType": "application/json",
            "ContentMD5": ANY,
            "Metadata": ANY,
            "IfNoneMatch": "*",
        }

    def test_failed_upload_retries_without_fetching(self) -> None:
        """Failed upload and restart retain identical bytes and identity."""
        with tempfile.TemporaryDirectory() as directory, Stubber(self.client) as stub:
            path = Path(directory)
            pending = path / "pending.json"
            pending.write_bytes(self.data)
            (path / "last.json").write_bytes(b"last good")
            stub.add_client_error(
                "put_object",
                service_error_code="ServiceUnavailable",
                http_status_code=503,
                expected_params=self.parameters,
            )
            stub.add_response("put_object", {}, self.parameters)
            with patch("collector.export_amsterdam", new_callable=AsyncMock) as fetch:
                with self.assertRaises(self.client.exceptions.ClientError):
                    run_once(self.client, "test", path)
                self.assertEqual(pending.read_bytes(), self.data)
                self.assertEqual((path / "last.json").read_bytes(), b"last good")
                self.assertEqual(run_once(self.client, "test", path), self.key)
                fetch.assert_not_awaited()
            self.assertFalse(pending.exists())
            self.assertEqual((path / "last.json").read_bytes(), self.data)
            stub.assert_no_pending_responses()

    def test_uncertain_upload_compares_remote_bytes(self) -> None:
        """Lost acknowledgement is recoverable; conflicting bytes never replace data."""
        for remote in (self.data, b"different"):
            with (
                self.subTest(remote=remote),
                tempfile.TemporaryDirectory() as directory,
                Stubber(self.client) as stub,
            ):
                path = Path(directory)
                pending = path / "pending.json"
                pending.write_bytes(self.data)
                stub.add_client_error(
                    "put_object",
                    service_error_code="PreconditionFailed",
                    http_status_code=412,
                    expected_params=self.parameters,
                )
                stub.add_response(
                    "get_object",
                    {
                        "Body": StreamingBody(io.BytesIO(remote), len(remote)),
                    },
                    {"Bucket": "test", "Key": self.key},
                )
                if remote == self.data:
                    self.assertEqual(run_once(self.client, "test", path), self.key)
                else:
                    with self.assertRaisesRegex(ValueError, "different bytes"):
                        run_once(self.client, "test", path)
                    self.assertEqual(pending.read_bytes(), self.data)
                stub.assert_no_pending_responses()

    def test_failed_fetch_preserves_last_delivery(self) -> None:
        """Source failure causes no upload and leaves the last good artifact intact."""
        with tempfile.TemporaryDirectory() as directory, Stubber(self.client):
            path = Path(directory)
            (path / "last.json").write_bytes(b"last good")
            with (
                patch("collector.export_amsterdam", side_effect=TimeoutError),
                self.assertRaises(TimeoutError),
            ):
                run_once(self.client, "test", path)
            self.assertEqual((path / "last.json").read_bytes(), b"last good")
            self.assertFalse((path / "pending.json").exists())

    def test_successful_fetch_uploads_saved_file(self) -> None:
        """The existing exporter feeds the uploader without another mapping layer."""

        async def collect(path: Path) -> None:
            path.write_bytes(self.data)  # noqa: ASYNC240 - tiny local test input

        with tempfile.TemporaryDirectory() as directory, Stubber(self.client) as stub:
            stub.add_response("put_object", {}, self.parameters)
            with patch("collector.export_amsterdam", side_effect=collect):
                run_once(self.client, "test", Path(directory))
            self.assertEqual((Path(directory) / "last.json").read_bytes(), self.data)

    def test_invalid_pending_is_retained_without_upload(self) -> None:
        """Corrupt or oversized disk state fails closed instead of refetching."""
        with tempfile.TemporaryDirectory() as directory, Stubber(self.client):
            pending = Path(directory) / "pending.json"
            pending.write_bytes(self.data)
            with patch("collector.MAX_BYTES", 1), self.assertRaises(ValueError):
                upload(self.client, "test", pending)
            self.assertEqual(pending.read_bytes(), self.data)
