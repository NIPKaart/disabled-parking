"""Manage the location data of Antwerpen."""

from antwerpen import ODPAntwerpen
from antwerpen.models import DisabledParking

from app.cities import City
from app.helper import centroid
from app.records import MunicipalRecord, capacity, identifier, orientation, text


class Municipality(City):
    """Manage the location data of Antwerpen."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Antwerpen",
            country="Belgium",
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

    def source_items(self, payload: dict) -> list[DisabledParking]:
        """Parse captured source rows with the installed universal package."""
        return [DisabledParking.from_dict(row) for row in payload["features"]]

    def normalize(self, item: DisabledParking) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.entry_id)
        latitude, longitude = centroid(item.coordinates)
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(item.number),
            street=text(None),
            orientation=orientation(item.orientation),
            geometry_method="vertex_average",
            source_created_at=item.created_at,
            source_updated_at=None,
            source_attributes={
                "destiny": item.destiny,
                "window_time": item.window_time,
                "status": item.status,
                "gis_id": item.gis_id,
            },
        )
