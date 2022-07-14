"""Scrape and upload parking data to NIPKaart system"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app.cities.germany import hamburg
from app.cities.netherlands import (
    amersfoort,
    amsterdam,
    arnhem,
    den_haag,
    eindhoven,
    groningen,
    zoetermeer,
)

if __name__ == "__main__":
    load_dotenv()
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
    city: str = os.getenv("CITY")

    print("--- Start program ---")
    if city.lower() == "amsterdam":
        # Amsterdam
        data_set = asyncio.run(amsterdam.async_get_locations())
        if bool(data_set):
            print(f"Data opgehaald van: {city}")
            # database.truncate("Amsterdam")
            amsterdam.upload(data_set)
    elif city.lower() == "arnhem":
        # Arnhem
        arnhem.download()
        # database.truncate("Arnhem")
        arnhem.upload()
    elif city.lower() == "amersfoort":
        # Amersfoort
        data_set = asyncio.run(amersfoort.async_get_locations())
        if bool(data_set):
            print(f"Data opgehaald van: {city}")
            # database.truncate("Amersfoort")
            amersfoort.upload(data_set)
    elif city.lower() == "eindhoven":
        # Eindhoven
        data_set = asyncio.run(eindhoven.async_get_locations(200))
        if bool(data_set):
            print(f"Data opgehaald van: {city}")
            # database.truncate("Eindhoven")
            eindhoven.upload(data_set)
    elif city.lower() == "denhaag":
        # Den Haag
        data_set = asyncio.run(den_haag.async_get_locations(limit=300))
        if bool(data_set):
            print(f"Data opgehaald van: {city}")
            # database.truncate("Den Haag")
            den_haag.upload(data_set)
    elif city.lower() == "hamburg":
        # Hamburg
        data_set = asyncio.run(hamburg.async_get_locations())
        if bool(data_set):
            print(f"Data opgehaald van: {city}")
            # database.truncate("Hamburg")
            hamburg.upload(data_set)
    elif city.lower() == "groningen":
        # Groningen
        groningen.download()
        groningen.upload()
    elif city.lower() == "zoetermeer":
        # Zoetermeer
        zoetermeer.download()
        # database.truncate("Zoetermeer")
        zoetermeer.upload()
