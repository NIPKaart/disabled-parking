"""Manage the location data of Namur."""
import datetime

import pytz
from namur import ODPNamur

from app.database import connection, cursor

MUNICIPALITY = "Namur"
GEOCODE = "BE-WNA"
PHONE_CODE = "03281"


async def async_get_locations(limit):
    """Get parking data from API.

    Args:
        limit (int): The number of parking lots to get.
    """
    async with ODPNamur() as client:
        locations = await client.parking_spaces(limit=limit, parking_type=3)
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
                            longitude=values(longitude),
                            latitude=values(latitude),
                            updated_at=values(updated_at)"""
            val = (
                location_id,
                int(22),
                int(19),
                str(MUNICIPALITY),
                str(item.street),
                1,
                float(item.longitude),
                float(item.latitude),
                bool(True),
                (
                    item.created_at
                    or datetime.datetime.now(tz=pytz.timezone("Europe/Brussels"))
                ).strftime("%Y-%m-%d %H:%M:%S"),
                (
                    item.updated_at
                    or datetime.datetime.now(tz=pytz.timezone("Europe/Brussels"))
                ).strftime("%Y-%m-%d %H:%M:%S"),
            )
            # Execute the query
            # print(val)
            cursor.execute(sql, val)
        connection.commit()
    except Exception as error:
        print(f"MySQL error: {error}")
    finally:
        print(f"Parking spaces found: {index}")
        print("---")
        print(f"{MUNICIPALITY} - DONE with database update")
