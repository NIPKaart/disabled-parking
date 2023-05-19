"""Manage the location data of Den Haag."""
import datetime
import json
import os

import aiohttp
import pytz

from app.cities import City
from app.database import connection, cursor


class Municipality(City):
    """Manage the location data of Den Haag."""

    def __init__(self):
        """Initialize the class."""
        super().__init__(
            name="Den Haag",
            country="Netherlands",
            country_id=157,
            province_id=9,
            geo_code="NL-ZH",
        )
        self.limit = 300
        self.cbs_code = "0518"

    async def async_get_locations(self):
        """Get the data from the CKAN API endpoint.

        Returns:
            List of objects from all parking lots.
        """
        async with aiohttp.ClientSession() as client:
            async with client.get(
                f'{os.getenv("CKAN_SOURCE")}/api/3/action/datastore_search?resource_id=6dd4aa05-31bf-4b98-b8d5-2560b6cb9740&limit={self.limit}'
            ) as resp:
                print(f"{self.name} - data has been retrieved")
                return json.loads(await resp.text())

    def number(self, value):
        """Convert the value to an integer.

        Args:
            value (str): The value to convert.

        Returns:
            int: The converted value.
        """
        if value is None:
            return 1
        return value

    def upload_data(self, data_set):
        """Upload the data from the JSON file to the database.

        Args:
            data_set (str): The data to upload.
        """
        index: int
        try:
            for index, item in enumerate(data_set["result"]["records"], 1):
                # Define unique id
                location_id = (
                    f"{self.geo_code}-{self.cbs_code}-{item['GUID'].split('{')[1]}"
                )

                # Make the sql query
                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, orientation, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
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
                    str(item["ORIENTATIE"]),
                    self.number(item["AANTALPLAATSEN"]),
                    float(item["LONG"]),
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
