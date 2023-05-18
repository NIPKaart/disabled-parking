"""Manage the location data of Amsterdam."""
import datetime

import pytz
from odp_amsterdam import ODPAmsterdam

from app.cities import City
from app.database import connection, cursor
from app.helper import centroid

MUNICIPALITY = "Amsterdam"
GEOCODE = "NL-NH"
CBS_CODE = "0363"


class Amsterdam(City):
    """Manage the location data of Amsterdam."""

    def __init__(self):
        """Initialize the class."""
        super().__init__(MUNICIPALITY, "Netherlands", GEOCODE, CBS_CODE)
        self.limit = 1500

    async def async_get_locations(self):
        """Get parking data from API.

        Returns:
            List of objects from all parking lots.
        """
        async with ODPAmsterdam() as client:
            locations = await client.locations(limit=self.limit, parking_type="E6a")
            print(f"Data retrieved from: {self.name}")
            return locations

    def correct_orientation(self, orientation_type) -> str:
        """Correct the orientation of the parking lot.

        Args:
            orientation_type (str): The orientation of the parking lot.

        Returns:
            str: The corrected orientation name.
        """
        if orientation_type == "Vissengraat":
            return str("Visgraat")
        return str(orientation_type)

    def upload_data(self, data_set):
        """Upload the data from the JSON file to the database.

        Args:
            data_set: The data_set to upload.
        """
        index: int
        try:
            for index, item in enumerate(data_set, 1):
                # Get the coordinates of the parking lot with centroid
                latitude, longitude = centroid(item.coordinates)
                # Define unique id
                location_id = f"{self.geo_code}-{self.cbs_code}-{item.spot_id}"

                # Make the sql query
                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, orientation, number, longitude, latitude, visibility, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
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
                    int(157),
                    int(8),
                    str(MUNICIPALITY),
                    str(item.street),
                    self.correct_orientation(item.orientation),
                    int(item.number),
                    float(longitude),
                    float(latitude),
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
            print(f"Parking spaces found: {index}")
            print("---")
            print(f"{MUNICIPALITY} - DONE with database update")
