"""Manage the location data of Dusseldorf."""

from dusseldorf import ODPDusseldorf

from app.cities import City


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
