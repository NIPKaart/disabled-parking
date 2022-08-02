"""Manage the location data of Amsterdam."""
import datetime
import json

import aiohttp
import pytz

from app.database import connection, cursor
from app.helper import centroid

MUNICIPALITY = "Amsterdam"
GEOCODE = "NL-NH"
CBS_CODE = "0363"


async def async_get_locations():
    """Get the data from the GeoJSON API endpoint."""
    async with aiohttp.ClientSession() as client:
        async with client.get(
            "https://api.data.amsterdam.nl/v1/parkeervakken/parkeervakken?eType=E6a&_format=geojson"
        ) as resp:
            return await resp.text()


def correct_orientation(orientation_type) -> str:
    """Correct the orientation of the parking lot.

    Args:
        orientation_type (str): The orientation of the parking lot.

    Returns:
        str: The corrected orientation name.
    """
    if orientation_type == "Vissengraat":
        return str("Visgraat")
    return str(orientation_type)


def upload(data_set):
    """Upload the data from the JSON file to the database."""
    amsterdam_obj = json.loads(data_set)
    index: int
    try:
        for index, item in enumerate(amsterdam_obj["features"], 1):
            # Get the coordinates of the parking lot with centroid
            latitude, longitude = centroid(item["geometry"]["coordinates"])
            # Define unique id
            location_id = f"{GEOCODE}-{CBS_CODE}-{item['id'].split('.')[1]}"

            item = item["properties"]
            # Make the sql query
            sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, orientation, number, longitude, latitude, visibility, created_at, updated_at)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
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
                int(8),
                str(MUNICIPALITY),
                str(item["straatnaam"]),
                correct_orientation(item["type"]),
                int(item["aantal"]),
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
        print(f"{index} - Parkeerplaatsen gevonden")
        print(f"{MUNICIPALITY} - KLAAR met updaten van database")
