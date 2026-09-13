"""Manage the location data of Brussel."""

from brussel import ODPBrussel

from app.cities import City


class Municipality(City):
    """Manage the location data of Brussel."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Brussel",
            country="Belgium",
            geo_code="BE-BRU",
        )
        self.limit = 1000
        self.phone_code = "0322"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPBrussel() as client:
            locations = await client.disabled_parkings(limit=self.limit)
            print(f"{self.name} - data has been retrieved")
            return locations
