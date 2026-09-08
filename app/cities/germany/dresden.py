"""Manage the location data of Dresden."""

from dresden import ODPDresden
from dresden.models import DisabledParking

from app.cities import City
from app.records import MunicipalRecord, capacity, identifier, text


class Municipality(City):
    """Manage the location data of Dresden."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Dresden",
            country="Germany",
            geo_code="DE-SN",
        )
        self.limit = 1000
        self.phone_code = "0351"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPDresden() as client:
            locations = await client.disabled_parkings(limit=self.limit)
            print(f"{self.name} - data has been retrieved")
            return locations

    def source_items(self, payload: dict) -> list[DisabledParking]:
        """Parse captured source rows with the installed universal package."""
        return [DisabledParking.from_dict(row) for row in payload["features"]]

    def normalize(self, item: DisabledParking) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.entry_id)
        latitude, longitude = item.latitude, item.longitude
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(item.number),
            street=text(None),
            orientation=None,
            geometry_method="source_point",
            source_created_at=item.created_at,
            source_updated_at=None,
            source_attributes={"usage_time": item.usage_time, "photo": item.photo},
        )
