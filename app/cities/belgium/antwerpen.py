"""Manage the location data of Antwerpen."""

from antwerpen import ODPAntwerpen

from app.cities import City


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
