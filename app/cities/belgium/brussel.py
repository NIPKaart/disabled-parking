"""Manage the location data of Brussel."""

import datetime

import pymysql
import pytz
from brussel import ODPBrussel
from brussel.models import DisabledParking

from app.cities import City
from app.records import MunicipalRecord, capacity, identifier, text


class Municipality(City):
    """Manage the location data of Brussel."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Brussel",
            country="Belgium",
            country_id=22,
            province_id=18,
            geo_code="BE-BRU",
        )
        self.limit = 1000
        self.phone_code = "0322"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPBrussel() as client:
            locations = await client.disabled_parkings(limit=self.limit)
            print(f"{self.name} - data has been retrieved")
            return locations

    def upload_data(self, data_set: list) -> None:
        """Upload the data set to the database.

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
                location_id = f"{self.geo_code}-{self.phone_code}-{item.spot_id}"
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
                    item.number or 1,
                    float(item.longitude),
                    float(item.latitude),
                    True,
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                    (
                        item.updated_at
                        or datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))
                    ),
                )
                cursor.execute(sql, val)
            connection.commit()
        except pymysql.Error as error:
            print(f"MySQL error: {error}")
        finally:
            print(f"{self.name} - parking spaces found: {count}")
            print("---")
            print(f"{self.name} - DONE with database update")

    def source_items(self, payload: dict) -> list[DisabledParking]:
        """Parse captured source rows with the installed universal package."""
        return [DisabledParking.from_dict(row) for row in payload["records"]]

    def normalize(self, item: DisabledParking) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.spot_id)
        latitude, longitude = item.latitude, item.longitude
        return MunicipalRecord(
            external_id=external_id,
            legacy_id=f"{self.source_id}-{external_id}",
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(item.number),
            street=text(item.address),
            orientation=None,
            geometry_method="source_point",
            source_created_at=None,
            source_updated_at=item.updated_at,
            source_attributes={},
        )
