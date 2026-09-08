"""Manage the location data of Zoetermeer."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.cities import City
from app.records import MunicipalRecord, capacity, identifier, text

load_dotenv()
env_path = Path() / ".env"
load_dotenv(dotenv_path=env_path)


class Municipality(City):
    """Manage the location data of Zoetermeer."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Zoetermeer",
            country="Netherlands",
            geo_code="NL-ZH",
        )
        self.cbs_code = "0637"
        self.local_file = "app/data/parking-zoetermeer.json"

    def download(self) -> None:
        """Download the data as JSON file."""
        # Create a variable and pass the url of file to be downloaded
        remote_url = (
            f"{os.getenv('ARCGIS_SOURCE')}/308bb3581ba646afad6f776a8f7e4e67_0.geojson"
        )
        # Make http request for remote file data
        data = requests.get(remote_url, timeout=10)
        # Save file data to local copy
        with Path(self.local_file).open("wb") as file:
            file.write(data.content)
        print(f"{self.name} - KLAAR met downloaden")

    def source_items(self, payload: dict) -> list[dict]:
        """Select the same source rows as the existing municipal adapter."""
        return payload["features"]

    def normalize(self, item: dict) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        location = item["properties"]
        latitude, longitude = location["lat"], location["lon"]
        external_id = identifier(location["OBJECTID_1"])
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(location.get("plaatsen")),
            street=text(None),
            orientation=None,
            identity_method="source_id",
            geometry_method="source_point",
            source_attributes={},
        )
