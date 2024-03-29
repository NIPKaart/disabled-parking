"""Manage the location data of Amersfoort."""

import datetime
import json
import os
from pathlib import Path

import aiohttp
import pymysql
import pytz
from dotenv import load_dotenv

from app.cities import City
from app.database import connection, cursor
from app.helper import centroid, get_unique_number

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
            country_id=157,
            province_id=7,
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
                f'{os.getenv("CKAN_SOURCE")}/dataset/280abd40-bd4a-4d76-9537-2c2bae526296/resource/417f3e35-4a5b-47c6-a23f-cbf92938c9e5/download/amersfoort-gehandicaptenparkeerplaatsen.json',
            ) as resp,
        ):
            print(f"{self.name} - data has been retrieved")
            return json.loads(await resp.text())

    def upload_data(self, data_set: list) -> None:
        """Upload the data from the JSON file to the database.

        Args:
        ----
            data_set: The data set to upload.

        """
        count: int = 0
        try:
            for item in data_set["features"]:
                count += 1
                # Get the coordinates of the parking lot with centroid
                latitude, longitude = centroid(item["geometry"]["coordinates"][0])
                # Define unique id
                location_id = f"{self.geo_code}-{self.cbs_code}-{get_unique_number(latitude, longitude)}"  # noqa: E501

                location = item["properties"]
                # Make the sql query
                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                        UPDATE id=values(id),
                                country_id=values(country_id),
                                province_id=values(province_id),
                                municipality=values(municipality),
                                street=values(street),
                                number=values(number),
                                longitude=values(longitude),
                                latitude=values(latitude),
                                updated_at=values(updated_at)"""  # noqa: E501
                val = (
                    location_id,
                    int(self.country_id),
                    int(self.province_id),
                    str(self.name),
                    str(location["STRAATNAAM"]),
                    int(location["AANTAL_PLAATSEN"]),
                    float(longitude),
                    float(latitude),
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
