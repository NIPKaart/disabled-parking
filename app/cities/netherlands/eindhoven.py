"""Manage the location data of Eindhoven."""

from eindhoven import ODPEindhoven

from app.cities import City


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
