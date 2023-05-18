"""Manage the location data of Groningen."""
import datetime
import json
import os
import urllib.request
from pathlib import Path

import pytz
from dotenv import load_dotenv

from app.cities import City
from app.database import connection, cursor
from app.helper import centroid

load_dotenv()
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class Municipality(City):
    """Manage the location data of Groningen."""

    def __init__(self):
        """Initialize the class."""
        super().__init__(
            name="Groningen",
            country="Netherlands",
            country_id=157,
            province_id=1,
            geo_code="NL-GR",
            cbs_code="0014",
        )

    def download(self):
        """Download the data as JSON file."""

        # Create a variable and pass the url of file to be downloaded
        url = f'{os.getenv("GRONINGEN_SOURCE")}/open-data/gemeentegroningen_parkeervakken.geojson'
        # Copy a network object to a local file
        urllib.request.urlretrieve(url, "app/data/parking-groningen.json")
        print(f"{self.name} - KLAAR met downloaden")

    def upload_json(self):
        """Upload the data from the JSON file to the database."""
        groningen_file = "app/data/parking-groningen.json"
        with open(groningen_file, "r", encoding="UTF-8") as groningen_data:
            groningen_obj = json.load(groningen_data)

        count: int = 0
        try:
            for item in groningen_obj["features"]:
                if item["properties"]["Vakfunctie"] == "Invaliden_alg":
                    count += 1
                    # Define unique id
                    location_id = (
                        f"{self.geo_code}-{self.cbs_code}-{item['properties']['VakID']}"
                    )
                    # Get the coordinates of the parking lot with centroid
                    latitude, longitude = centroid(item["geometry"]["coordinates"])
                    item = item["properties"]

                    # Make the sql query
                    sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, number, latitude, longitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                        UPDATE id=values(id),
                                country_id=values(country_id),
                                province_id=values(province_id),
                                municipality=values(municipality),
                                street=values(street),
                                number=values(number),
                                latitude=values(latitude),
                                longitude=values(longitude),
                                updated_at=values(updated_at)"""
                    val = (
                        location_id,
                        int(self.country_id),
                        int(self.province_id),
                        str(self.name),
                        str(item["Straatnaam"]),
                        int(1),
                        float(latitude),
                        float(longitude),
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
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")
