"""Download and upload disabled parking data to NIPKaart platform."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app.cities.netherlands import amsterdam
from app.database import truncate  # pylint: disable=unused-import # noqa: F401


class CityProvider:
    """Class to provide the correct city."""

    def provide_city(self, city: str):
        """Provide the correct city.

        Args:
            city (str): The city to provide.
        """
        if city == "amsterdam":
            return amsterdam.Amsterdam()
        raise ValueError("City not found")


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)

    cp = CityProvider()

    # Get the city from the environment variables
    selected_city: str = os.getenv("CITY").lower()
    provided_city = cp.provide_city(selected_city)

    # Get the data from the API
    data_set = asyncio.run(provided_city.async_get_locations())
    print(data_set)
