"""Manage the location data of Den Haag."""
import datetime
import json
import os

import aiohttp
import pytz

from app.database import connection, cursor

MUNICIPALITY = "Den Haag"
GEOCODE = "NL-ZH"
CBS_CODE = "0518"


async def async_get_locations(limit):
    """Get the data from the CKAN API endpoint."""
    async with aiohttp.ClientSession() as client:
        async with client.get(
            f'{os.getenv("CKAN_SOURCE")}/api/3/action/datastore_search?resource_id=6dd4aa05-31bf-4b98-b8d5-2560b6cb9740&limit={limit}'
        ) as resp:
            return await resp.text()


def number(value):
    """Convert the value to an integer.

    Args:
        value (str): The value to convert.

    Returns:
        int: The converted value.
    """
    if value is None:
        return 1
    return value


def upload(data_set):
    """Upload the data from the JSON file to the database.

    Args:
        data_set (str): The data to upload.
    """
    den_haag_obj = json.loads(data_set)
    index: int
    try:
        for index, item in enumerate(den_haag_obj["result"]["records"], 1):
            # Define unique id
            location_id = f"{GEOCODE}-{CBS_CODE}-{item['GUID'].split('{')[1]}"
            sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, orientation, number, longitude, latitude, visibility, created_at, updated_at)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                     UPDATE id=values(id),
                            country_id=values(country_id),
                            province_id=values(province_id),
                            municipality=values(municipality),
                            street=values(street),
                            orientation=values(orientation),
                            number=values(number),
                            longitude=values(longitude),
                            latitude=values(latitude),
                            updated_at=values(updated_at)"""
            val = (
                location_id,
                int(157),
                int(9),
                str(MUNICIPALITY),
                str(item["ORIENTATIE"]),
                number(item["AANTALPLAATSEN"]),
                float(item["LONG"]),
                float(item["LAT"]),
                bool(True),
                (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
            )
            cursor.execute(sql, val)
        connection.commit()
    except Exception as error:
        print(f"MySQL error: {error}")
    finally:
        print(f"{index} - Parkeerplaatsen gevonden")
        print(f"{MUNICIPALITY} - KLAAR met updaten van database")
