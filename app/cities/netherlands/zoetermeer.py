"""Manage the location data of Zoetermeer."""

import datetime
import json
import os
from pathlib import Path

import pymysql
import pytz
import requests
from dotenv import load_dotenv

from app.cities import City
from app.database import connection, cursor

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
            country_id=157,
            province_id=9,
            geo_code="NL-ZH",
        )
        self.cbs_code = "0637"
        self.local_file = "app/data/parking-zoetermeer.json"

    def download(self) -> None:
        """Download the data as JSON file."""
        # Create a variable and pass the url of file to be downloaded
        remote_url = (
            f'{os.getenv("ARCGIS_SOURCE")}/308bb3581ba646afad6f776a8f7e4e67_0.geojson'
        )
        # Make http request for remote file data
        data = requests.get(remote_url, timeout=10)
        # Save file data to local copy
        with Path(self.local_file).open("wb") as file:
            file.write(data.content)
        print(f"{self.name} - KLAAR met downloaden")

    def upload_json(self) -> None:
        """Upload the data from the JSON file to the database."""
        with Path(self.local_file).open(encoding="UTF-8") as zoetermeer_data:
            zoetermeer_obj = json.load(zoetermeer_data)

        count: int = 0
        try:
            for item in zoetermeer_obj["features"]:
                count += 1
                location = item["properties"]
                # Define unique id
                location_id = (
                    f"{self.geo_code}-{self.cbs_code}-{location['OBJECTID_1']}"
                )

                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                        UPDATE id=values(id),
                                country_id=values(country_id),
                                province_id=values(province_id),
                                municipality=values(municipality),
                                street=values(street),
                                orientation=values(orientation),
                                number=values(number),
                                longitude=values(longitude),
                                latitude=values(latitude),
                                updated_at=values(updated_at)"""  # noqa: E501
                val = (
                    location_id,
                    int(self.country_id),
                    int(self.province_id),
                    str(self.name),
                    int(location["plaatsen"]),
                    float(location["lon"]),
                    float(location["lat"]),
                    True,
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                )
                cursor.execute(sql, val)
            connection.commit()
        except pymysql.Error as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")
