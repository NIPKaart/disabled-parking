"""Manage the location data of Amsterdam."""

import datetime

import pymysql
import pytz
from odp_amsterdam import ODPAmsterdam
from odp_amsterdam.models import ParkingSpot

from app.cities import City
from app.helper import centroid
from app.records import MunicipalRecord, capacity, identifier, orientation, text


class Municipality(City):
    """Manage the location data of Amsterdam."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Amsterdam",
            country="Netherlands",
            country_id=157,
            province_id=8,
            geo_code="NL-NH",
        )
        self.limit = 2000
        self.cbs_code = "0363"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            List of objects from all parking lots.

        """
        async with ODPAmsterdam() as client:
            locations = await client.locations(limit=self.limit, parking_type="E6a")
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
        if orientation_type == "Vissengraat":
            return "Visgraat"
        return str(orientation_type)

    def upload_data(self, data_set: list) -> None:
        """Upload the data from the JSON file to the database.

        Args:
        ----
            data_set: The data set to upload.

        """
        # Database initialization belongs only to the legacy SQL path.
        # pylint: disable-next=import-outside-toplevel
        from app.database import connection, cursor  # noqa: PLC0415

        count: int = 0
        try:
            for item in data_set:
                count += 1
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
                                updated_at=values(updated_at)"""  # noqa: E501
                val = (
                    location_id,
                    int(self.country_id),
                    int(self.province_id),
                    str(self.name),
                    str(item.street),
                    self.correct_orientation(item.orientation),
                    int(item.number),
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

    def source_items(self, payload: dict) -> list[ParkingSpot]:
        """Parse captured source rows with the installed universal package."""
        items = []
        for row in payload["features"]:
            expected_number = capacity(row["properties"]["aantal"])
            item = ParkingSpot.from_json(row)
            if item.number != expected_number:
                raise ValueError(row["properties"]["aantal"])
            items.append(item)
        return items

    def normalize(self, item: ParkingSpot) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.spot_id)
        latitude, longitude = centroid(item.coordinates)
        return MunicipalRecord(
            external_id=external_id,
            legacy_id=f"{self.source_id}-{external_id}",
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(item.number),
            street=text(item.street),
            orientation=orientation(item.orientation),
            geometry_method="vertex_average",
            source_created_at=None,
            source_updated_at=None,
            source_attributes={
                "spot_type": item.spot_type,
                "spot_description": item.spot_description,
            },
        )
