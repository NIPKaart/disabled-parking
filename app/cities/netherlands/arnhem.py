"""Manage the location data of Arnhem."""
import datetime
import json
import os
import urllib.request
from pathlib import Path

import pytz
from dotenv import load_dotenv

from app.cities import City
from app.database import connection, cursor

load_dotenv()
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class Municipality(City):
    """Manage the location data of Arnhem."""

    def __init__(self):
        """Initialize the class."""
        super().__init__(
            name="Arnhem",
            country="Netherlands",
            country_id=157,
            province_id=6,
            geo_code="NL-GE",
            cbs_code="0202",
        )

    def download(self):
        """Download the data as JSON file."""

        # Create a variable and pass the url of file to be downloaded
        url = f'{os.getenv("ARCGIS_SOURCE")}/6f301547133a4acda9074ec3ca9b075b_0.geojson'
        # Copy a network object to a local file
        urllib.request.urlretrieve(url, "app/data/parking-arnhem.json")
        print(f"{self.name} - KLAAR met downloaden")

    def upload_data(self):
        """Upload the data from the JSON file to the database."""

        arnhem_file = "app/data/parking-arnhem.json"
        with open(arnhem_file, "r", encoding="UTF-8") as arnhem_data:
            arnhem_obj = json.load(arnhem_data)

        index: int
        try:
            for index, item in enumerate(arnhem_obj["features"], 1):
                item = item["properties"]
                # Generate unique id
                location_id = f"{self.geo_code}-{self.cbs_code}-{item['OBJECTID']}"

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
                                updated_at=values(updated_at)"""
                val = (
                    location_id,
                    int(self.country_id),
                    int(self.province_id),
                    str(self.name),
                    str(item["LOCATIE"]),
                    str(item["TYPE_VAK"]),
                    int(item["AANTAL"]),
                    float(item["LON"]),
                    float(item["LAT"]),
                    bool(True),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                )
                # print(val)
                cursor.execute(sql, val)
            connection.commit()
        except Exception as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {index}")
            print("---")
            print(f"{self.name} - DONE with database update")
