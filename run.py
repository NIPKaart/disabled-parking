"""Download and upload disabled parking data to NIPKaart platform."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app import database
from app.cities.netherlands import (
    amersfoort,
    amsterdam,
    arnhem,
    den_haag,
    eindhoven,
    groningen,
)


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
        if city == "arnhem":
            return arnhem.Municipality()
        if city == "den haag":
            return den_haag.Municipality()
        if city == "eindhoven":
            return eindhoven.Municipality()
        if city == "groningen":
            return groningen.Municipality()
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
    if selected_city in ["groningen", "arnhem"]:
        data_set = None  # pylint: disable=C0103
        provided_city.download()
    else:
        data_set = asyncio.run(provided_city.async_get_locations())

    # Truncate and upload new data to the database
    database.truncate(provided_city.name)
    # Upload the data to the database
    if data_set:
        provided_city.upload_data(data_set)
    else:
        provided_city.upload_json()
