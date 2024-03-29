"""Manage the location data of Hamburg."""

import datetime

import pymysql
import pytz
from hamburg import UDPHamburg

from app.cities import City
from app.database import connection, cursor


class Municipality(City):
    """Manage the location data of Hamburg."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Hamburg",
            country="Germany",
            country_id=83,
            province_id=14,
            geo_code="DE-HH",
        )
        self.phone_code = "040"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with UDPHamburg() as client:
            locations = await client.disabled_parkings(limit=1000)
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
                # Define unique id
                location_id = f"{self.geo_code}-{self.phone_code}-{item.spot_id[-4:]}"
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
                    str(item.street),
                    item.number,
                    float(item.longitude),
                    float(item.latitude),
                    True,
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Berlin"))),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Berlin"))),
                )
                if item.number is not None:
                    count += 1
                    cursor.execute(sql, val)
            connection.commit()
        except pymysql.Error as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")
