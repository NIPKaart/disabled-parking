"""Manage the location data of Antwerpen."""

import pymysql
from antwerpen import ODPAntwerpen

from app.cities import City
from app.database import connection, cursor


class Municipality(City):
    """Manage the location data of Antwerpen."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Antwerpen",
            country="Belgium",
            country_id=22,
            province_id=13,
            geo_code="BE-VAN",
        )
        self.limit = 1000
        self.phone_code = "0323"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.
        """
        async with ODPAntwerpen() as client:
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
                cursor.execute(sql, val)
            connection.commit()
        except pymysql.Error as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")
