"""Manage the location data of Eindhoven."""

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
            number=capacity(item.number),
            street=text(item.street),
            orientation=None,
            geometry_method="source_point",
            source_created_at=None,
            source_updated_at=item.updated_at,
            source_attributes={"parking_type": item.parking_type},
        )
