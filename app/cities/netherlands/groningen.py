"""Manage the location data of Groningen."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.cities import City
from app.helper import centroid
from app.records import MunicipalRecord, identifier, text

load_dotenv()
env_path = Path() / ".env"
load_dotenv(dotenv_path=env_path)


class Municipality(City):
    """Manage the location data of Groningen."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Groningen",
            country="Netherlands",
            geo_code="NL-GR",
        )
        self.cbs_code = "0014"
        self.local_file = "app/data/parking-groningen.json"

    def download(self) -> None:
        """Download the data as JSON file."""
        # Create a variable and pass the url of file to be downloaded
        remote_url = f"{os.getenv('GRONINGEN_SOURCE')}/open-data/gemeentegroningen_parkeervakken.geojson"  # noqa: E501
        # Make http request for remote file data
        data = requests.get(remote_url, timeout=10)
        # Save file data to local copy
        with Path(self.local_file).open("wb") as file:
            file.write(data.content)
        print(f"{self.name} - KLAAR met downloaden")

    def source_items(self, payload: dict) -> list[dict]:
        """Select the same source rows as the existing municipal adapter."""
        return [
            row
            for row in payload["features"]
            if row["properties"]["Vakfunctie"] == "Invaliden_alg"
        ]

    def normalize(self, item: dict) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        location = item["properties"]
        latitude, longitude = centroid(item["geometry"]["coordinates"][0])
        external_id = identifier(location["VakID"])
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=None,
            street=text(location.get("Straatnaam")),
            orientation=None,
            identity_method="source_id",
            geometry_method="vertex_average",
            source_attributes={"parking_type": location["Vakfunctie"]},
        )
