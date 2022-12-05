"""Download and upload disabled parking data to NIPKaart platform."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app.cities.belgium import brussel, liege, namur
from app.cities.germany import dresden, dusseldorf, hamburg
from app.cities.netherlands import (
    amersfoort,
    amsterdam,
    arnhem,
    den_haag,
    eindhoven,
    groningen,
    zoetermeer,
)
from app.database import truncate  # pylint: disable=unused-import # noqa: F401

if __name__ == "__main__":
    load_dotenv()
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
    city: str = os.getenv("CITY")
    city = city.lower()

    print("--- Start program ---")
    if city == "amsterdam":
        # Amsterdam - NL
        data_set = asyncio.run(amsterdam.async_get_locations(limit=2000))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Amsterdam")
            amsterdam.upload(data_set)
    elif city == "arnhem":
        # Arnhem - NL
        arnhem.download()
        # truncate("Arnhem")
        arnhem.upload()
    elif city == "amersfoort":
        # Amersfoort -NL
        data_set = asyncio.run(amersfoort.async_get_locations())
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Amersfoort")
            amersfoort.upload(data_set)
    elif city == "brussel":
        # Brussels - BE
        data_set = asyncio.run(brussel.async_get_locations(limit=1000))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Brussel")
            brussel.upload(data_set)
    elif city == "denhaag":
        # Den Haag - NL
        data_set = asyncio.run(den_haag.async_get_locations(limit=300))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Den Haag")
            den_haag.upload(data_set)
    elif city == "dusseldorf":
        # Dusseldorf - DE
        data_set = asyncio.run(dusseldorf.async_get_locations(limit=350))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Dusseldorf")
            dusseldorf.upload(data_set)
    elif city == "dresden":
        # Dresden - DE
        data_set = asyncio.run(dresden.async_get_locations(limit=500))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Dresden")
            dresden.upload(data_set)
    elif city == "eindhoven":
        # Eindhoven - NL
        data_set = asyncio.run(eindhoven.async_get_locations(limit=200))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Eindhoven")
            eindhoven.upload(data_set)
    elif city == "hamburg":
        # Hamburg - DE
        data_set = asyncio.run(hamburg.async_get_locations())
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Hamburg")
            hamburg.upload(data_set)
    elif city == "liege":
        # Liege - BE
        data_set = asyncio.run(liege.async_get_locations(limit=1000))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Liege")
            liege.upload(data_set)
    elif city == "namur":
        # Namur - BE
        data_set = asyncio.run(namur.async_get_locations(limit=1000))
        if data_set:
            print(f"Data retrieved from: {city}")
            # truncate("Namur")
            namur.upload(data_set)
    elif city == "groningen":
        # Groningen
        groningen.download()
        # truncate("Groningen")
        groningen.upload()
    elif city == "zoetermeer":
        # Zoetermeer
        zoetermeer.download()
        # truncate("Zoetermeer")
        zoetermeer.upload()
    else:
        print(f"{city} is currently not supported")
