"""Manage the location data of Dresden."""

from dresden import ODPDresden

from app.cities import City


class Municipality(City):
    """Manage the location data of Dresden."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Dresden",
            country="Germany",
            geo_code="DE-SN",
        )
        self.limit = 1000
        self.phone_code = "0351"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPDresden() as client:
            locations = await client.disabled_parkings(limit=self.limit)
            print(f"{self.name} - data has been retrieved")
            return locations
