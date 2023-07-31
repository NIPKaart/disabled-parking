"""Manage the location data of Arnhem."""
import datetime

import pymysql
import pytz
from arnhem import ODPArnhem

from app.cities import City
from app.database import connection, cursor
from app.helper import centroid


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
        self.limit = 200
        self.cbs_code = "0202"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            List of objects from all parking lots.
        """
        async with ODPArnhem() as client:
            locations = await client.locations(
                limit=self.limit,
                set_filter="RVV_SOORT='E6a'",
            )
            print(f"{self.name} - data has been retrieved")
            return locations

    def upload_data(self, data_set: list) -> None:
        """Upload the data_set to the database.

        Args:
        ----
            data_set: The data set to upload.
        """
        count: int = 0
        try:
            for item in data_set:
                count += 1
                # Get the coordinates of the parking lot with centroid
                latitude, longitude = centroid(item.coordinates)
                # Generate unique id
                location_id = f"{self.geo_code}-{self.cbs_code}-{item.spot_id}"

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
                    1,
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
