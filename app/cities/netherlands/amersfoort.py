"""Manage the location data of Amersfoort."""

import json
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

from app.cities import City

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
