"""Manage the location data of Dresden."""
import datetime

import pymysql
import pytz
from dresden import ODPDresden

from app.cities import City
from app.database import connection, cursor


class Municipality(City):
    """Manage the location data of Dresden."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Dresden",
            country="Germany",
            country_id=83,
            province_id=20,
            geo_code="DE-SN",
        )
        self.limit = 1000
        self.phone_code = "0351"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.
        """
        async with ODPDresden() as client:
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
                location_id = f"{self.geo_code}-{self.phone_code}-{item.entry_id}"
                # Make the sql query
                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                        UPDATE id=values(id),
                                country_id=values(country_id),
                                province_id=values(province_id),
                                municipality=values(municipality),
                                number=values(number),
                                longitude=values(longitude),
                                latitude=values(latitude),
                                updated_at=values(updated_at)"""  # noqa: E501
                val = (
                    location_id,
                    int(self.country_id),
                    int(self.province_id),
                    str(self.name),
                    item.number or 1,
                    float(item.longitude),
                    float(item.latitude),
                    bool(True),
                    item.created_at,
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
