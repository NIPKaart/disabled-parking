"""Manage the location data of Dusseldorf."""
import datetime

import pytz
from dusseldorf import ODPDusseldorf

from app.database import connection, cursor

MUNICIPALITY = "Dusseldorf"
GEOCODE = "DE-NW"
PHONE_CODE = "0211"


async def async_get_locations():
    """Get parking data from API."""
    async with ODPDusseldorf() as client:
        locations = await client.disabled_parkings(limit=350)
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
            location_id = f"{GEOCODE}-{PHONE_CODE}-{item.entry_id}"
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
                int(83),
                int(16),
                str(MUNICIPALITY),
                str(item.address),
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
