"""Download and upload disabled parking data to NIPKaart platform."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app import database
from app.cities.provider import CityProvider

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    env_path = Path() / ".env"
    load_dotenv(dotenv_path=env_path)

    cp = CityProvider()
    print("--- Start program ---")

    # Get the city from the environment variables
    selected_city: str = os.getenv("CITY").lower()
    provided_city = cp.provide_city(selected_city)

    # Get the data from the API
    if selected_city in ["groningen", "zoetermeer"]:
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
