"""Manage the location data of Liege."""

import datetime

import pymysql
import pytz
from liege import ODPLiege

from app.cities import City
from app.database import connection, cursor
from app.helper import get_unique_number


class Municipality(City):
    """Manage the location data of Liege."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Liege",
            country="Belgium",
            country_id=22,
            province_id=17,
            geo_code="BE-WLG",
        )
        self.limit = 1000
        self.phone_code = "0324"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPLiege() as client:
            locations = await client.disabled_parkings(limit=self.limit)
            print(f"{self.name} - data has been retrieved")
            return locations

    def upload_data(self, data_set: list) -> None:
        """Upload the data set to the database.

        Args:
        ----
            data_set: The data set to upload.

        """
        count: int = 0
        try:
            for item in data_set:
                count += 1
                # Define unique id
                location_id = f"{self.geo_code}-{self.phone_code}-{get_unique_number(item.latitude, item.longitude)}"  # noqa: E501
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
                    str(item.address),
                    item.number or 1,
                    float(item.longitude),
                    float(item.latitude),
                    True,
                    (
                        item.created_at
                        or datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))
                    ),
                    (
                        item.updated_at
                        or datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))
                    ),
                )
                cursor.execute(sql, val)
            connection.commit()
        except pymysql.Error as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")
