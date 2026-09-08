"""Manage the location data of Arnhem."""

from arnhem import ODPArnhem
from arnhem.models import ParkingSpot

from app.cities import City
from app.helper import centroid
from app.records import MunicipalRecord, identifier, text


class Municipality(City):
    """Manage the location data of Arnhem."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Arnhem",
            country="Netherlands",
            geo_code="NL-GE",
        )
        self.limit = 200
        self.cbs_code = "0202"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            List of objects from all parking lots.

        """
        async with ODPArnhem() as client:
            locations = await client.locations(
                limit=self.limit,
                set_filter="RVV_SOORT='E6a'",
            )
            print(f"{self.name} - data has been retrieved")
            return locations

    def source_items(self, payload: dict) -> list[ParkingSpot]:
        """Parse captured source rows with the installed universal package."""
        return [ParkingSpot.from_json(row) for row in payload["features"]]

    def normalize(self, item: ParkingSpot) -> MunicipalRecord:
        """Translate the existing municipal fields without writing to the database."""
        external_id = identifier(item.spot_id)
        latitude, longitude = centroid(item.coordinates)
        return MunicipalRecord(
            external_id=external_id,
            latitude=float(latitude),
            longitude=float(longitude),
            number=None,
            street=text(item.street),
            orientation=None,
            geometry_method="vertex_average",
            source_created_at=None,
            source_updated_at=None,
            source_attributes={
                "parking_type": item.parking_type,
                "traffic_sign": item.traffic_sign,
                "neighborhood_code": item.neighborhood_code,
                "district_code": item.district_code,
            },
        )
