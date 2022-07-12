import datetime, pytz
from hamburg import UDPHamburg
from database import connection, cursor

municipality = "Hamburg"

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
    count: int
    try:
        for index, item in enumerate(data_set, 1):
            count = index
            sql = """INSERT INTO `parking_cities` (`id`, `country_id`, `province_id`, `municipality`, `street`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
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
            val = (item.spot_id, int(83), int(14), str(municipality), str(item.street), None, item.number, float(item.longitude),
                   float(item.latitude), bool(True), (datetime.datetime.now(tz=pytz.timezone('Europe/Amsterdam'))),
                   (datetime.datetime.now(tz=pytz.timezone('Europe/Amsterdam'))))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f"Aantal parkeerplaatsen gevonden: {count}")
        print(f'{municipality} - KLAAR met updaten van database')