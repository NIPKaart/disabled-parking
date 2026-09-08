"""Manage the location data of Amsterdam."""

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
