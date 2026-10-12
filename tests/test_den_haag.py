"""Verify Den Haag's original IDs, WFS completeness and safe delivery."""
# ruff: noqa: PT009, PT027

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import boto3
from botocore.stub import ANY, Stubber

from app.cities.netherlands.den_haag import Municipality
from app.export import export_dataset
from app.records import SourceError
from collector import run_once


def feature(identifier: int = 1, capacity: object = None) -> dict:
    """Keep small examples in the original municipal vocabulary."""
    return {
        "type": "Feature",
        "id": "ephemeral-geoserver-id",
        "geometry": {"type": "Point", "coordinates": [4.3, 52.08]},
        "properties": {
            "ID": identifier,
            "GUID": "original-guid",
            "CAPACITEIT": capacity,
            "ORIENTATIE": "File",
            "GEBRUIKSDOEL": "Gehandicapte algemeen",
            "OMSCHRIJVING": "Maximaal 2 uur",
            "BEGINDATUM": "2013-04-11",
            "EINDDATUM": None,
        },
    }


def page(*features: dict, total: int | None = None) -> dict:
    """Describe a real WFS page without inventing a dataset revision."""
    return {
        "type": "FeatureCollection",
        "numberMatched": total or len(features),
        "numberReturned": len(features),
        "features": list(features),
        "crs": {"properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
    }


class DenHaagTests(unittest.IsolatedAsyncioTestCase):
    """Exercise complete collection, source mapping and atomic exports offline."""

    async def test_http_error_prevents_a_collection(self) -> None:
        """Fail on HTTP errors before accepting source JSON."""
        with patch("app.cities.netherlands.den_haag.aiohttp.ClientSession") as factory:
            client = factory.return_value.__aenter__.return_value
            client.get = MagicMock()
            response = client.get.return_value.__aenter__.return_value
            response.raise_for_status = MagicMock(
                side_effect=aiohttp.ClientResponseError(MagicMock(), (), status=503)
            )
            response.json = AsyncMock()
            with self.assertRaises(SourceError):
                await Municipality().collect()
            response.json.assert_not_awaited()

    async def test_request_preserves_longitude_first_and_original_id_order(
        self,
    ) -> None:
        """The real HTTP method asks for the agreed WFS layer and page offset."""
        client = MagicMock()
        response = client.get.return_value.__aenter__.return_value
        response.raise_for_status = MagicMock()
        response.json = AsyncMock(return_value=page(feature()))
        await Municipality().request(client, 100)
        parameters = client.get.call_args.kwargs["params"]
        self.assertEqual(parameters["srsName"], "EPSG:4326")
        self.assertEqual(parameters["sortBy"], "ID")
        self.assertEqual(parameters["startIndex"], 100)
        response.raise_for_status.assert_called_once()

    async def test_pagination_preserves_claims_and_ignores_ephemeral_ids(self) -> None:
        """Retain unknown and zero capacity, mixed access and original descriptions."""
        first, second = feature(), feature(2, 0)
        second["properties"]["GEBRUIKSDOEL"] = "Gehandicapte algemeen, Laden en lossen"
        second["properties"]["ORIENTATIE"] = None
        repeated = copy.deepcopy(first)
        repeated["id"] = "different-ephemeral-id"
        with (
            patch("app.cities.netherlands.den_haag.PAGE_SIZE", 1),
            patch.object(Municipality, "request", new_callable=AsyncMock) as request,
            tempfile.TemporaryDirectory() as directory,
        ):
            request.side_effect = [
                page(first, total=2),
                page(second, total=2),
                page(repeated, total=2),
            ]
            output = Path(directory) / "delivery.json"
            self.assertEqual(await export_dataset("den-haag", output), 2)
            data = json.loads(output.read_bytes())
        self.assertEqual([call.args[1] for call in request.await_args_list], [0, 1, 0])
        self.assertEqual(data["dataset"], "nl-den-haag")
        self.assertEqual(data["source_count"], 2)
        self.assertIsNone(data["source"]["licence"])
        row = data["records"][0]
        self.assertEqual(row["external_id"], "1")
        self.assertEqual(row["geometry"], first["geometry"])
        self.assertEqual(row["source_attributes"], first["properties"])
        self.assertEqual(row["access_category"], "general")
        self.assertEqual(row["orientation"], "parallel")
        self.assertIsNone(row["number"])
        self.assertIsNone(row["street"])
        self.assertIsNone(row["source_updated_at"])
        self.assertEqual(data["records"][1]["number"], 0)
        self.assertEqual(data["records"][1]["access_category"], "unknown")

    async def test_failed_retrieval_keeps_last_export(self) -> None:
        """Reject duplicates, short/extra pages, changing counts and source errors."""
        first = page(feature(), total=2)
        changed = feature()
        changed["properties"]["CAPACITEIT"] = 3
        cases = [
            [page()],
            [page(feature(), total=10001)],
            [first, page(feature(), total=2)],
            [first, page(total=2)],
            [first, page(feature(2), total=3)],
            [first, page(feature(2), feature(3), total=2)],
            [first, page(feature(2), total=2), page(changed, total=2)],
            [TimeoutError()],
            [aiohttp.ClientConnectionError()],
        ]
        wrong_crs = page(feature())
        wrong_crs["crs"]["properties"]["name"] = "EPSG:28992"
        cases.append([wrong_crs])
        for field, value in [
            ("numberMatched", True),
            ("numberMatched", "2"),
            ("numberReturned", True),
            ("numberReturned", 2),
        ]:
            malformed = page(feature())
            malformed[field] = value
            cases.append([malformed])
        for responses in cases:
            with (
                self.subTest(responses=responses),
                patch("app.cities.netherlands.den_haag.PAGE_SIZE", 1),
                patch.object(
                    Municipality, "request", new_callable=AsyncMock
                ) as request,
                tempfile.TemporaryDirectory() as directory,
            ):
                request.side_effect = responses
                output = Path(directory) / "last.json"
                output.write_bytes(b"last good")
                with self.assertRaises(SourceError):
                    await export_dataset("den-haag", output)
                self.assertEqual(output.read_bytes(), b"last good")

    def test_invalid_identity_access_capacity_and_geometry_are_rejected(self) -> None:
        """Personal reservations and invalid coordinates cannot enter a delivery."""
        for field, value in [
            ("ID", True),
            ("ID", 0),
            ("ID", 1.5),
            ("ID", "1"),
            ("GEBRUIKSDOEL", "Gehandicapte op kenteken"),
            ("GEBRUIKSDOEL", "Gehandicapte algemeen, Gehandicapte op kenteken"),
            ("GEBRUIKSDOEL", None),
            ("CAPACITEIT", -1),
            ("CAPACITEIT", 1.5),
        ]:
            source = feature()
            source["properties"][field] = value
            with (
                self.subTest(field=field, value=value),
                self.assertRaises((ValueError, TypeError)),
            ):
                Municipality().normalize(source)
        for coordinates in (
            [52.08, 200],
            [True, 52],
            [4, float("nan")],
            [4],
            [4, 52, 1],
        ):
            source = feature()
            source["geometry"]["coordinates"] = coordinates
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                Municipality().normalize(source)


class DenHaagCollectorTests(unittest.TestCase):
    """Use the existing immutable upload with dataset-specific pending state."""

    def test_delivery_uses_registered_prefix(self) -> None:
        """Run the actual adapter through the shared collector with stubbed S3."""
        client = boto3.client(
            "s3",
            region_name="auto",
            aws_access_key_id="test",
            aws_secret_access_key="test",  # noqa: S106 - dummy stub credentials
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(Municipality, "request", new_callable=AsyncMock) as request,
            Stubber(client) as stub,
        ):
            request.side_effect = [page(feature()), page(feature())]
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
            key = run_once(client, "test", Path(directory), "den-haag")
            saved = json.loads(
                (Path(directory) / "nl-den-haag" / "last.json").read_bytes()
            )
            self.assertEqual(key, f"municipal/nl-den-haag/{saved['delivery_id']}.json")
            self.assertFalse(
                (Path(directory) / "nl-den-haag" / "pending.json").exists()
            )
            stub.assert_no_pending_responses()
