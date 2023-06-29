"""Manage the location data of Arnhem."""
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
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class Municipality(City):
    """Manage the location data of Arnhem."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Arnhem",
            country="Netherlands",
            country_id=157,
            province_id=6,
            geo_code="NL-GE",
        )
        self.cbs_code = "0202"
        self.local_file = "app/data/parking-arnhem.json"

    def download(self) -> None:
        """Download the data as JSON file."""
        # Create a variable and pass the url of file to be downloaded
        remote_url = (
            f'{os.getenv("ARCGIS_SOURCE")}/6f301547133a4acda9074ec3ca9b075b_0.geojson'
        )
        # Make http request for remote file data
        data = requests.get(remote_url, timeout=10)
        # Save file data to local copy
        with Path(self.local_file).open("wb") as file:
            file.write(data.content)
        print(f"{self.name} - KLAAR met downloaden")

    def upload_json(self) -> None:
        """Upload the data from the JSON file to the database."""
        with Path(self.local_file).open(encoding="UTF-8") as arnhem_data:
            arnhem_obj = json.load(arnhem_data)

        count: int = 0
        try:
            for item in arnhem_obj["features"]:
                count += 1
                location = item["properties"]
                # Generate unique id
                location_id = f"{self.geo_code}-{self.cbs_code}-{location['OBJECTID']}"

                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, orientation, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
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
                    str(location["LOCATIE"]),
                    str(location["TYPE_VAK"]),
                    int(location["AANTAL"]),
                    float(location["LON"]),
                    float(location["LAT"]),
                    bool(True),
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
