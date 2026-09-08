"""Manage the location data of Hamburg."""

from koeln import StadtKoeln
from koeln.models import DisabledParking

from app.cities import City
from app.records import MunicipalRecord, capacity, identifier, text


class Municipality(City):
    """Manage the location data of Hamburg."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Köln",
            country="Germany",
            geo_code="DE-NW",
        )
        self.phone_code = "0221"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with StadtKoeln() as client:
            locations = await client.disabled_parkings()
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
            source_created_at=None,
            source_updated_at=None,
            source_attributes={
                "note": item.note,
                "district": item.district,
                "district_nr": item.district_nr,
            },
        )
