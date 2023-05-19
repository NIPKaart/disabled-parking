"""Download and upload disabled parking data to NIPKaart platform."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app import database
from app.cities.belgium import brussel, liege, namur
from app.cities.netherlands import (
    amersfoort,
    amsterdam,
    arnhem,
    den_haag,
    eindhoven,
    groningen,
    zoetermeer,
)


class CityProvider:
    """Class to provide the correct city."""

    def provide_city(self, city_name: str):
        """Provide the correct city.

        Args:
            city_name (str): The city to provide.
        """
        match city_name:
            case "amersfoort":
                city_class = amersfoort.Municipality()
            case "amsterdam":
                city_class = amsterdam.Municipality()
            case "arnhem":
                city_class = arnhem.Municipality()
            case "brussel":
                city_class = brussel.Municipality()
            case "den haag":
                city_class = den_haag.Municipality()
            case "eindhoven":
                city_class = eindhoven.Municipality()
            case "groningen":
                city_class = groningen.Municipality()
            case "liege":
                city_class = liege.Municipality()
            case "namur":
                city_class = namur.Municipality()
            case "zoetermeer":
                city_class = zoetermeer.Municipality()
            case _:
                raise ValueError(f"{city_name} is not a valid city.")
        return city_class


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
    if selected_city in ["groningen", "arnhem", "zoetermeer"]:
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
