"""Manage the location data of Namur."""

from namur import ODPNamur
from namur.models import ParkingSpot

from app.cities import City
from app.records import MunicipalRecord, identifier, text


class Municipality(City):
    """Manage the location data of Namur."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Namur",
            country="Belgium",
            geo_code="BE-WNA",
        )
        self.limit = 1000
        self.phone_code = "03281"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPNamur() as client:
            locations = await client.parking_spaces(limit=self.limit, parking_type=3)
            print(f"{self.name} - data has been retrieved")
            return locations

    def source_items(self, payload: dict) -> list[ParkingSpot]:
        """Parse captured source rows with the installed universal package."""
        return [ParkingSpot.from_json(row) for row in payload["records"]]

    def normalize(self, item: ParkingSpot) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.spot_id)
        latitude, longitude = item.latitude, item.longitude
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=None,
            street=text(item.street),
            orientation=None,
            geometry_method="source_point",
            source_created_at=item.created_at,
            source_updated_at=item.updated_at,
            source_attributes={"parking_type": item.parking_type},
        )
