"""Manage the location data of Namur."""

from namur import ODPNamur

from app.cities import City


class Municipality(City):
    """Manage the location data of Namur."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Namur",
            country="Belgium",
            geo_code="BE-WNA",
        )
        self.limit = 1000
        self.phone_code = "03281"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with ODPNamur() as client:
            locations = await client.parking_spaces(limit=self.limit, parking_type=3)
            print(f"{self.name} - data has been retrieved")
            return locations
