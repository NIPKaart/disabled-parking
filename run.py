"""Download and upload disabled parking data to NIPKaart platform."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app import database
from app.cities.netherlands import amersfoort, amsterdam


class CityProvider:
    """Class to provide the correct city."""

    def provide_city(self, city: str):
        """Provide the correct city.

        Args:
            city (str): The city to provide.
        """
        if city == "amersfoort":
            return amersfoort.Municipality()
        if city == "amsterdam":
            return amsterdam.Municipality()
        raise ValueError(f"{city} is not a valid city.")


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)

    cp = CityProvider()
    print("--- Start program ---")

    # Get the city from the environment variables
    selected_city: str = os.getenv("CITY").lower()
    provided_city = cp.provide_city(selected_city)

    # Get the data from the API
    data_set = asyncio.run(provided_city.async_get_locations())
    if data_set:
        # Truncate and upload new data to the database
        database.truncate(provided_city.name)
        provided_city.upload_data(data_set)
