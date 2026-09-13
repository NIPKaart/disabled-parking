"""Manage the location data of Arnhem."""

from arnhem import ODPArnhem

from app.cities import City


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
