"""Manage the location data of Dusseldorf."""
import datetime

import pymysql
import pytz
from dusseldorf import ODPDusseldorf

from app.cities import City
from app.database import connection, cursor


class Municipality(City):
    """Manage the location data of Dusseldorf."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Dusseldorf",
            country="Germany",
            country_id=83,
            province_id=16,
            geo_code="DE-NW",
        )
        self.phone_code = "0211"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.
        """
        async with ODPDusseldorf() as client:
            locations = await client.disabled_parkings()
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
                    item.number,
                    float(item.longitude),
                    float(item.latitude),
                    bool(True),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Berlin"))),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Berlin"))),
                )
                cursor.execute(sql, val)
            connection.commit()
        except pymysql.Error as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")
