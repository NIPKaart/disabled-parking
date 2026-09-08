"""Manage the location data of Eindhoven."""

import datetime

import pymysql
import pytz
from eindhoven import ODPEindhoven
from eindhoven.models import ParkingSpot

from app.cities import City
from app.records import MunicipalRecord, capacity, identifier, text


class Municipality(City):
    """Manage the location data of Eindhoven."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Eindhoven",
            country="Netherlands",
            country_id=157,
            province_id=11,
            geo_code="NL-NB",
        )
        self.limit = 200
        self.cbs_code = "0772"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            List of objects from all parking lots.

        """
        async with ODPEindhoven() as client:
            locations = await client.locations(limit=self.limit, parking_type=3)
            print(f"{self.name} - data has been retrieved")
            return locations

    def upload_data(self, data_set: list) -> None:
        """Upload the data_set to the database.

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
                # Define unique id
                location_id = f"{self.geo_code}-{self.cbs_code}-{item.spot_id}"
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
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                    item.updated_at,
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
        return [ParkingSpot.from_json(row) for row in payload["records"]]

    def normalize(self, item: ParkingSpot) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.spot_id)
        latitude, longitude = item.latitude, item.longitude
        return MunicipalRecord(
            external_id=external_id,
            legacy_id=f"{self.source_id}-{external_id}",
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(item.number),
            street=text(item.street),
            orientation=None,
            geometry_method="source_point",
            source_created_at=None,
            source_updated_at=item.updated_at,
            source_attributes={"parking_type": item.parking_type},
        )
