"""Manage the location data of Namur."""
import datetime

import pytz
from namur import ODPNamur

from app.cities import City
from app.database import connection, cursor


class Municipality(City):
    """Manage the location data of Namur."""

    def __init__(self):
        """Initialize the class."""
        super().__init__(
            name="Namur",
            country="Belgium",
            country_id=22,
            province_id=19,
            geo_code="BE-WNA",
        )
        self.limit = 1000
        self.phone_code = "03281"

    async def async_get_locations(self):
        """Get parking data from API.

        Returns:
            list: A list of parking locations.
        """
        async with ODPNamur() as client:
            locations = await client.parking_spaces(limit=self.limit, parking_type=3)
            print(f"{self.name} - data has been retrieved")
            return locations

    def upload(self, data_set):
        """Upload the data set to the database.

        Args:
            data_set: The data set to upload.
        """
        index: int
        try:
            for index, item in enumerate(data_set, 1):
                # Define unique id
                location_id = f"{self.geo_code}-{self.phone_code}-{item.spot_id}"
                # Make the sql query
                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                        UPDATE id=values(id),
                                country_id=values(country_id),
                                province_id=values(province_id),
                                municipality=values(municipality),
                                street=values(street),
                                longitude=values(longitude),
                                latitude=values(latitude),
                                updated_at=values(updated_at)"""
                val = (
                    location_id,
                    int(self.country_id),
                    int(self.province_id),
                    str(self.name),
                    str(item.street),
                    1,
                    float(item.longitude),
                    float(item.latitude),
                    bool(True),
                    (
                        item.created_at
                        or datetime.datetime.now(tz=pytz.timezone("Europe/Brussels"))
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    (
                        item.updated_at
                        or datetime.datetime.now(tz=pytz.timezone("Europe/Brussels"))
                    ).strftime("%Y-%m-%d %H:%M:%S"),
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
