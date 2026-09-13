"""Manage the location data of Hamburg."""

from koeln import StadtKoeln

from app.cities import City


class Municipality(City):
    """Manage the location data of Hamburg."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Köln",
            country="Germany",
            geo_code="DE-NW",
        )
        self.phone_code = "0221"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            list: A list of parking locations.

        """
        async with StadtKoeln() as client:
            locations = await client.disabled_parkings()
            print(f"{self.name} - data has been retrieved")
            return locations
