"""Manage the location data of Hamburg."""

from hamburg import UDPHamburg

from app.cities import City


class Municipality(City):
    """Manage the location data of Hamburg."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Hamburg",
            country="Germany",
            geo_code="DE-HH",
        )
        self.phone_code = "040"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with UDPHamburg() as client:
            locations = await client.disabled_parkings(limit=1000)
            print(f"{self.name} - data has been retrieved")
            return locations
