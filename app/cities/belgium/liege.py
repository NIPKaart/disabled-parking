"""Manage the location data of Liege."""

from liege import ODPLiege

from app.cities import City


class Municipality(City):
    """Manage the location data of Liege."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Liege",
            country="Belgium",
            geo_code="BE-WLG",
        )
        self.limit = 1000
        self.phone_code = "0324"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPLiege() as client:
            locations = await client.disabled_parkings(limit=self.limit)
            print(f"{self.name} - data has been retrieved")
            return locations
