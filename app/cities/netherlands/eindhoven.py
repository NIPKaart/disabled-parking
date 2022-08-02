"""Manage the location data of Eindhoven."""
import datetime

import pytz
from parking_eindhoven import ParkingEindhoven

from app.database import connection, cursor

MUNICIPALITY = "Eindhoven"
GEOCODE = "NL-NB"
CBS_CODE = "0772"


async def async_get_locations(number):
    """Get parking data from API.

    Args:
        number (int): The number of parking lots to get.
    """
    async with ParkingEindhoven(parking_type=3) as client:
        locations = await client.locations(rows=number)
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
            location_id = f"{GEOCODE}-{CBS_CODE}-{item.spot_id}"
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
                int(11),
                str(MUNICIPALITY),
                str(item.street),
                item.number,
                float(item.longitude),
                float(item.latitude),
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
