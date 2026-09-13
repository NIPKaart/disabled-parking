"""Manage the location data of Amsterdam."""

from odp_amsterdam import ODPAmsterdam

from app.cities import City


class Municipality(City):
    """Manage the location data of Amsterdam."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(
            name="Amsterdam",
            country="Netherlands",
            geo_code="NL-NH",
        )
        self.limit = 2000
        self.cbs_code = "0363"

    async def async_get_locations(self) -> list:
        """Get parking data from API.

        Returns
        -------
            List of objects from all parking lots.

        """
        async with ODPAmsterdam() as client:
            locations = await client.locations(limit=self.limit, parking_type="E6a")
            print(f"{self.name} - data has been retrieved")
            return locations
