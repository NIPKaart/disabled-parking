"""Scrape and upload parking data to NIPKaart system"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app.cities.belgium import liege
from app.cities.germany import dusseldorf, hamburg
from app.cities.netherlands import (
    amersfoort,
    amsterdam,
    arnhem,
    den_haag,
    eindhoven,
    groningen,
    zoetermeer,
)

# import app.database as database

if __name__ == "__main__":
    load_dotenv()
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
    city: str = os.getenv("CITY")
    city = city.lower()

    print("--- Start program ---")
    if city == "amsterdam":
        # Amsterdam - NL
        data_set = asyncio.run(amsterdam.async_get_locations())
        if bool(data_set):
            print(f"Data retrieved from: {city}")
            # database.truncate("Amsterdam")
            amsterdam.upload(data_set)
    elif city == "arnhem":
        # Arnhem - NL
        arnhem.download()
        # database.truncate("Arnhem")
        arnhem.upload()
    elif city == "amersfoort":
        # Amersfoort -NL
        data_set = asyncio.run(amersfoort.async_get_locations())
        if bool(data_set):
            print(f"Data retrieved from: {city}")
            # database.truncate("Amersfoort")
            amersfoort.upload(data_set)
    elif city == "denhaag":
        # Den Haag - NL
        data_set = asyncio.run(den_haag.async_get_locations(limit=300))
        if bool(data_set):
            print(f"Data retrieved from: {city}")
            # database.truncate("Den Haag")
            den_haag.upload(data_set)
    elif city == "dusseldorf":
        # Dusseldorf - DE
        data_set = asyncio.run(dusseldorf.async_get_locations(limit=350))
        if bool(data_set):
            print(f"Data retrieved from: {city}")
            # database.truncate("Dusseldorf")
            dusseldorf.upload(data_set)
    elif city == "eindhoven":
        # Eindhoven - NL
        data_set = asyncio.run(eindhoven.async_get_locations(limit=200))
        if bool(data_set):
            print(f"Data retrieved from: {city}")
            # database.truncate("Eindhoven")
            eindhoven.upload(data_set)
    elif city == "hamburg":
        # Hamburg - DE
        data_set = asyncio.run(hamburg.async_get_locations())
        if bool(data_set):
            print(f"Data retrieved from: {city}")
            # database.truncate("Hamburg")
            hamburg.upload(data_set)
    elif city == "liege":
        # Liege - BE
        data_set = asyncio.run(liege.async_get_locations(limit=1000))
        if bool(data_set):
            print(f"Data retrieved from: {city}")
            # database.truncate("Liege")
            liege.upload(data_set)
    elif city == "groningen":
        # Groningen
        groningen.download()
        # database.truncate("Groningen")
        groningen.upload()
    elif city == "zoetermeer":
        # Zoetermeer
        zoetermeer.download()
        # database.truncate("Zoetermeer")
        zoetermeer.upload()
