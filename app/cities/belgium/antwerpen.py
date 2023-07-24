"""Manage the location data of Antwerpen."""
import datetime

import pymysql
import pytz
from antwerpen import ODPAntwerpen

from app.cities import City
from app.database import connection, cursor
from app.helper import centroid


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
        self.limit = 1800
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

    def correct_orientation(self, orientation_type: str) -> str:
        """Correct the orientation of the parking lot.

        Args:
        ----
            orientation_type (str): The orientation of the parking lot.

        Returns:
        -------
            str: The corrected orientation name.
        """
        if orientation_type == "Dwars":
            return "Haaks"
        if orientation_type == "Schuin":
            return "Vissengraat"
        return str(orientation_type)

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
                # Get the coordinates of the parking lot with centroid
                latitude, longitude = centroid(item.coordinates)
                # Define unique id
                location_id = f"{self.geo_code}-{self.phone_code}-{item.entry_id}"
                # Make the sql query
                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, orientation, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                        UPDATE id=values(id),
                                country_id=values(country_id),
                                province_id=values(province_id),
                                municipality=values(municipality),
                                orientation=values(orientation),
                                number=values(number),
                                longitude=values(longitude),
                                latitude=values(latitude),
                                visibility=values(visibility),
                                updated_at=values(updated_at)"""  # noqa: E501
                val = (
                    location_id,
                    int(self.country_id),
                    int(self.province_id),
                    self.name,
                    self.correct_orientation(item.orientation),
                    int(item.number),
                    float(longitude),
                    float(latitude),
                    bool(True),
                    item.created_at,
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Brussels"))),
                )
                cursor.execute(sql, val)
            connection.commit()
        except pymysql.Error as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")
