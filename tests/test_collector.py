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

from collector import run_once, upload

DATASET = "nl-amsterdam"
EINDHOVEN_DATASET = "nl-eindhoven"


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
            root = Path(directory)
            path = root / DATASET
            path.mkdir()
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
            with patch("collector.export_dataset", new_callable=AsyncMock) as fetch:
                with self.assertRaises(self.client.exceptions.ClientError):
                    run_once(self.client, "test", root)
                self.assertEqual(pending.read_bytes(), self.data)
                self.assertEqual((path / "last.json").read_bytes(), b"last good")
                self.assertEqual(run_once(self.client, "test", root), self.key)
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
                root = Path(directory)
                path = root / DATASET
                path.mkdir()
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
                    self.assertEqual(run_once(self.client, "test", root), self.key)
                else:
                    with self.assertRaisesRegex(ValueError, "different bytes"):
                        run_once(self.client, "test", root)
                    self.assertEqual(pending.read_bytes(), self.data)
                stub.assert_no_pending_responses()

    def test_failed_fetch_preserves_last_delivery(self) -> None:
        """Source failure causes no upload and leaves the last good artifact intact."""
        with tempfile.TemporaryDirectory() as directory, Stubber(self.client):
            root = Path(directory)
            path = root / DATASET
            path.mkdir()
            (path / "last.json").write_bytes(b"last good")
            with (
                patch("collector.export_dataset", side_effect=TimeoutError),
                self.assertRaises(TimeoutError),
            ):
                run_once(self.client, "test", root)
            self.assertEqual((path / "last.json").read_bytes(), b"last good")
            self.assertFalse((path / "pending.json").exists())

    def test_successful_fetch_uploads_saved_file(self) -> None:
        """The existing exporter feeds the uploader without another mapping layer."""

        async def collect(_city: str, path: Path) -> None:
            path.write_bytes(self.data)  # noqa: ASYNC240 - tiny local test input

        with tempfile.TemporaryDirectory() as directory, Stubber(self.client) as stub:
            stub.add_response("put_object", {}, self.parameters)
            with patch("collector.export_dataset", side_effect=collect):
                run_once(self.client, "test", Path(directory))
            self.assertEqual(
                (Path(directory) / DATASET / "last.json").read_bytes(), self.data
            )

    def test_invalid_pending_is_retained_without_upload(self) -> None:
        """Corrupt or oversized disk state fails closed instead of refetching."""
        with tempfile.TemporaryDirectory() as directory, Stubber(self.client):
            pending = Path(directory) / "pending.json"
            pending.write_bytes(self.data)
            with patch("collector.MAX_BYTES", 1), self.assertRaises(ValueError):
                upload(self.client, "test", pending)
            self.assertEqual(pending.read_bytes(), self.data)

    def test_eindhoven_retry_state_is_separate_from_amsterdam(self) -> None:
        """Keep Amsterdam retry state intact when an Eindhoven upload fails."""
        data = json.loads(self.data)
        data["dataset"] = EINDHOVEN_DATASET
        raw = json.dumps(data).encode()
        key = f"municipal/{EINDHOVEN_DATASET}/{data['delivery_id']}.json"
        parameters = {**self.parameters, "Key": key, "Body": raw}
        with tempfile.TemporaryDirectory() as directory, Stubber(self.client) as stub:
            path = Path(directory)
            (path / DATASET).mkdir()
            (path / DATASET / "pending.json").write_bytes(self.data)
            (path / "nl-eindhoven").mkdir()
            pending = path / "nl-eindhoven" / "pending.json"
            pending.write_bytes(raw)
            stub.add_client_error(
                "put_object",
                service_error_code="ServiceUnavailable",
                http_status_code=503,
                expected_params=parameters,
            )
            stub.add_response("put_object", {}, parameters)
            with patch("collector.export_dataset", new_callable=AsyncMock) as fetch:
                with self.assertRaises(self.client.exceptions.ClientError):
                    run_once(self.client, "test", path, "eindhoven")
                self.assertEqual(pending.read_bytes(), raw)
                self.assertEqual(run_once(self.client, "test", path, "eindhoven"), key)
                fetch.assert_not_awaited()
            self.assertEqual((path / DATASET / "pending.json").read_bytes(), self.data)
            self.assertEqual((path / "nl-eindhoven" / "last.json").read_bytes(), raw)
            stub.assert_no_pending_responses()

    def test_wrong_dataset_cannot_be_uploaded_under_another_city(self) -> None:
        """A misplaced pending file is retained for diagnosis without a PUT."""
        with tempfile.TemporaryDirectory() as directory, Stubber(self.client):
            path = Path(directory)
            (path / "nl-eindhoven").mkdir()
            pending = path / "nl-eindhoven" / "pending.json"
            pending.write_bytes(self.data)
            with self.assertRaisesRegex(ValueError, "another dataset"):
                run_once(self.client, "test", path, "eindhoven")
            self.assertEqual(pending.read_bytes(), self.data)

    def test_eindhoven_fetch_feeds_the_correct_dataset_prefix(self) -> None:
        """First-run routing reaches Eindhoven and persists its own last delivery."""
        data = json.loads(self.data)
        data["dataset"] = EINDHOVEN_DATASET
        raw = json.dumps(data).encode()
        key = f"municipal/{EINDHOVEN_DATASET}/{data['delivery_id']}.json"

        async def collect(_city: str, path: Path) -> None:
            path.write_bytes(raw)  # noqa: ASYNC240 - tiny local test input

        with tempfile.TemporaryDirectory() as directory, Stubber(self.client) as stub:
            stub.add_response(
                "put_object", {}, {**self.parameters, "Key": key, "Body": raw}
            )
            with patch("collector.export_dataset", side_effect=collect):
                self.assertEqual(
                    run_once(self.client, "test", Path(directory), "eindhoven"), key
                )
            self.assertEqual(
                (Path(directory) / "nl-eindhoven" / "last.json").read_bytes(), raw
            )
