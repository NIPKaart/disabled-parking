"""Manage the location data of Amersfoort."""
import datetime
import json
import os
import urllib.request
from pathlib import Path

import aiohttp
import pytz
from dotenv import load_dotenv

from app.database import connection, cursor
from app.helper import centroid, get_unique_number

MUNICIPALITY = "Amersfoort"
GEOCODE = "NL-UT"
CBS_CODE = "0307"

load_dotenv()
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


async def async_get_locations():
    """Get the data from the CKAN API endpoint."""
    async with aiohttp.ClientSession() as client:
        async with client.get(
            f'{os.getenv("CKAN_SOURCE")}/dataset/280abd40-bd4a-4d76-9537-2c2bae526296/resource/417f3e35-4a5b-47c6-a23f-cbf92938c9e5/download/amersfoort-gehandicaptenparkeerplaatsen.json'
        ) as resp:
            return await resp.text()


def download():
    """Download the data as JSON file."""

    # Create a variable and pass the url of file to be downloaded
    url = f'{os.getenv("CKAN_SOURCE")}/download/amersfoort-gehandicaptenparkeerplaatsen.json'
    # Copy a network object to a local file
    urllib.request.urlretrieve(url, "data/parking-amersfoort.json")
    print(f"{MUNICIPALITY} - KLAAR met downloaden")


def upload(data_set):
    """Upload the data from the JSON file to the database."""
    amersfoort_obj = json.loads(data_set)
    count: int
    try:
        for index, item in enumerate(amersfoort_obj["features"], 1):
            count = index

            # Get the coordinates of the parking lot with centroid
            latitude, longitude = centroid(item["geometry"]["coordinates"])
            # Define unique id
            location_id = (
                f"{GEOCODE}-{CBS_CODE}-{get_unique_number(latitude, longitude)}"
            )

            item = item["properties"]
            # Make the sql query
            sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, number, longitude, latitude, visibility, created_at, updated_at)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                     UPDATE id=values(id),
                            country_id=values(country_id),
                            province_id=values(province_id),
                            municipality=values(municipality),
                            street=values(street),
                            number=values(number),
                            longitude=values(longitude),
                            latitude=values(latitude),
                            updated_at=values(updated_at)"""
            val = (
                location_id,
                int(157),
                int(7),
                str(MUNICIPALITY),
                str(item["STRAATNAAM"]),
                int(item["AANTAL_PLAATSEN"]),
                float(longitude),
                float(latitude),
                bool(True),
                (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
            )
            cursor.execute(sql, val)
        connection.commit()
    except Exception as error:
        print(f"MySQL error: {error}")
    finally:
        print(f"{count} - Parking spaces found")
        print("---")
        print(f"{MUNICIPALITY} - DONE with database update")
