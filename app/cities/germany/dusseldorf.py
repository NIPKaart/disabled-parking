"""Manage the location data of Dusseldorf."""

from dusseldorf import ODPDusseldorf
from dusseldorf.models import DisabledParking

from app.cities import City
from app.records import MunicipalRecord, capacity, identifier, text


class Municipality(City):
    """Manage the location data of Dusseldorf."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Dusseldorf",
            country="Germany",
            geo_code="DE-NW",
        )
        self.phone_code = "0211"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPDusseldorf() as client:
            locations = await client.disabled_parkings()
            print(f"{self.name} - data has been retrieved")
            return locations

    def source_items(self, payload: dict) -> list[DisabledParking]:
        """Parse captured source rows with the installed universal package."""
        items = []
        for row in payload["features"]:
            expected_number = capacity(row["properties"]["anzahl"].split()[0])
            item = DisabledParking.from_dict(row)
            if item.number != expected_number:
                raise ValueError(row["properties"]["anzahl"])
            items.append(item)
        return items

    def normalize(self, item: DisabledParking) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.entry_id)
        latitude, longitude = item.latitude, item.longitude
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=capacity(item.number),
            street=text(item.address),
            orientation=None,
            geometry_method="source_point",
            source_created_at=None,
            source_updated_at=item.last_update.date(),
            source_attributes={
                "time_limit": item.time_limit,
                "note": item.note,
                "district": item.district,
            },
        )
