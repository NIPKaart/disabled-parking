"""Exercise registration through the same CLI and collector used by real sources."""
# ruff: noqa: PT009

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import boto3
from botocore.stub import ANY, Stubber

from app.datasets import DATASETS, Dataset
from app.records import Collection
from collector import run_once
from export import main


class ExampleSource:
    """Supply a normalized fixture without importing a city-specific package."""

    async def collect(self) -> Collection:
        """Return complete source evidence for a registered test dataset."""
        return Collection(
            [
                {
                    "external_id": "source-1",
                    "geometry": {"type": "Point", "coordinates": [5, 51]},
                }
            ],
            total_count=1,
            pages_fetched=1,
            complete=True,
        )


class DatasetTests(unittest.TestCase):
    """A new registration alone must route both export and collection."""

    def test_registered_source_reaches_cli_and_its_own_bucket_prefix(self) -> None:
        """No exporter, CLI or collector city branch is needed for another source."""
        dataset = Dataset("nl-example", "all", ExampleSource)
        client = boto3.client(
            "s3",
            region_name="auto",
            aws_access_key_id="test",
            aws_secret_access_key="test",  # noqa: S106 - dummy SDK stub credentials
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(DATASETS, {"example": dataset}),
            redirect_stdout(io.StringIO()),
        ):
            output = Path(directory) / "example.json"
            with patch(
                "sys.argv", ["export.py", "--city", "example", "--output", str(output)]
            ):
                main()
            payload = json.loads(output.read_bytes())
            self.assertEqual(payload["dataset"], "nl-example")
            self.assertEqual(payload["selection"], "all")
            with Stubber(client) as stub:
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
                key = run_once(client, "test", Path(directory), "example")
                saved = json.loads(
                    (Path(directory) / "nl-example" / "last.json").read_bytes()
                )
                self.assertEqual(
                    key, f"municipal/nl-example/{saved['delivery_id']}.json"
                )
                stub.assert_no_pending_responses()
