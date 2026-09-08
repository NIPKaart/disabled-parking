"""Manage the location data of Amersfoort."""

import json
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

from app.cities import City
from app.helper import centroid, get_unique_number
from app.records import MunicipalRecord, capacity, identifier, text

load_dotenv()
env_path = Path() / ".env"
load_dotenv(dotenv_path=env_path)


class Municipality(City):
    """Manage the location data of Amersfoort."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Amersfoort",
            country="Netherlands",
            geo_code="NL-UT",
        )
        self.cbs_code = "0307"

    async def async_get_locations(self) -> json:
        """Get the data from the CKAN API endpoint.

        Returns
        -------
            List of objects from all parking lots.

        """
        async with (
            aiohttp.ClientSession() as client,
            client.get(
                f"{os.getenv('CKAN_SOURCE')}/dataset/280abd40-bd4a-4d76-9537-2c2bae526296/resource/417f3e35-4a5b-47c6-a23f-cbf92938c9e5/download/amersfoort-gehandicaptenparkeerplaatsen.json",
            ) as resp,
        ):
            print(f"{self.name} - data has been retrieved")
            return json.loads(await resp.text())

    def source_items(self, payload: dict) -> list[dict]:
        """Select the same source rows as the existing municipal adapter."""
        return payload["features"]

    def normalize(self, item: dict) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        location = item["properties"]
        latitude, longitude = centroid(item["geometry"]["coordinates"][0])
        external_id = identifier(get_unique_number(latitude, longitude))
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(location["AANTAL_PLAATSEN"]),
            street=text(location.get("STRAATNAAM")),
            orientation=None,
            identity_method="coordinate_hash",
            geometry_method="vertex_average",
            source_attributes={},
        )
