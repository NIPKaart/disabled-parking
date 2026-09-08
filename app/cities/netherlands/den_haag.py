"""Manage the location data of Den Haag."""

import json
import os

import aiohttp

from app.cities import City
from app.records import MunicipalRecord, capacity, identifier, orientation, text


class Municipality(City):
    """Manage the location data of Den Haag."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Den Haag",
            country="Netherlands",
            geo_code="NL-ZH",
        )
        self.limit = 300
        self.cbs_code = "0518"

    async def async_get_locations(self) -> list:
        """Get the data from the CKAN API endpoint.

        Returns
        -------
            List of objects from all parking lots.

        """
        async with (
            aiohttp.ClientSession() as client,
            client.get(
                f"{os.getenv('CKAN_SOURCE')}/api/3/action/datastore_search?resource_id=6dd4aa05-31bf-4b98-b8d5-2560b6cb9740&limit={self.limit}",
            ) as resp,
        ):
            print(f"{self.name} - data has been retrieved")
            return json.loads(await resp.text())

    def source_items(self, payload: dict) -> list[dict]:
        """Select the same source rows as the existing municipal adapter."""
        return payload["result"]["records"]

    def normalize(self, item: dict) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item["GUID"]).strip("{}")
        latitude, longitude = item["LAT"], item["LONG"]
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(item.get("AANTALPLAATSEN")),
            street=text(None),
            orientation=orientation(item.get("ORIENTATIE")),
            identity_method="source_id",
            geometry_method="source_point",
            source_attributes={},
        )
