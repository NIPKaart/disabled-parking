"""Manage the location data of Brussel."""
import datetime

import pytz
from brussel import ODPBrussel

from app.database import connection, cursor

MUNICIPALITY = "Brussel"
GEOCODE = "BE-BRU"
PHONE_CODE = "0322"


async def async_get_locations(limit):
    """Get parking data from API.

    Args:
        limit (int): The number of parking lots to get.
    """
    async with ODPBrussel() as client:
        locations = await client.disabled_parkings(limit=limit)
        return locations


def upload(data_set):
    """Upload the data_set to the database.

    Args:
        data_set: The data_set to upload.
    """
    index: int
    try:
        for index, item in enumerate(data_set, 1):
            # Define unique id
            location_id = f"{GEOCODE}-{PHONE_CODE}-{item.spot_id}"
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
                int(22),
                int(18),
                str(MUNICIPALITY),
                str(item.address),
                item.number or 1,
                float(item.longitude),
                float(item.latitude),
                bool(True),
                (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                (
                    item.updated_at
                    or datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))
                ),
            )
            # print(val)
            cursor.execute(sql, val)
        connection.commit()
    except Exception as error:
        print(f"MySQL error: {error}")
    finally:
        print(f"Parking spaces found: {index}")
        print("---")
        print(f"{MUNICIPALITY} - DONE with database update")
