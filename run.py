"""Scrape and upload parking data to NIPKaart system"""
import database as database
import asyncio, os

from dotenv import load_dotenv
from pathlib import Path

if __name__ == '__main__':
    load_dotenv()
    env_path = Path('.')/'.env'
    load_dotenv(dotenv_path=env_path)
    city: str = os.getenv("CITY")

    print("--- Start program ---")
    if city.lower() == "amsterdam":
        import cities.amsterdam as amsterdam
        # Amsterdam
        data_set = asyncio.run(amsterdam.async_get_locations())
        if (bool(data_set)):
            print(f"Data opgehaald van: {city}")
            database.truncate("Amsterdam")
            amsterdam.upload(data_set)
    elif city.lower() == "arnhem":
        import cities.arnhem as arnhem
        arnhem.download()
        # arnhem.upload()
    elif city.lower() == "amersfoort":
        import cities.amersfoort as amersfoort
        data_set = asyncio.run(amersfoort.async_get_locations())
        if (bool(data_set)):
            print(f"Data opgehaald van: {city}")
            amersfoort.upload(data_set)
    elif city.lower() == "eindhoven":
        import cities.eindhoven as eindhoven
        # Eindhoven
        data_set = asyncio.run(eindhoven.async_get_locations(200))
        if (bool(data_set)):
            print(f"Data opgehaald van: {city}")
            database.truncate("Eindhoven")
            eindhoven.upload(data_set)
    elif city.lower() == "denhaag":
        import cities.den_haag as den_haag
        # Den Haag
        den_haag.upload()
    elif city.lower() == "zoetermeer":
        import cities.zoetermeer as zoetermeer
        zoetermeer.download()
        # zoetermeer.upload()