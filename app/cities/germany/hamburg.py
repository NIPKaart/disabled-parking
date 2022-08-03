"""Manage the location data of Hamburg."""
import datetime

import pytz
from hamburg import UDPHamburg

from app.database import connection, cursor

MUNICIPALITY = "Hamburg"


async def async_get_locations():
    """Get parking data from API."""
    async with UDPHamburg() as client:
        locations = await client.disabled_parkings(bulk="true")
        return locations


def upload(data_set):
    """Upload the data_set to the database.

    Args:
        data_set: The data_set to upload.
    """
    index: int
    try:
        for index, item in enumerate(data_set, 1):
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
                item.spot_id.replace(".", "-"),
                int(83),
                int(14),
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
        print(f"Parking spaces found: {index}")
        print("---")
        print(f"{MUNICIPALITY} - DONE with database update")
