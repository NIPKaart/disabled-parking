import uuid, datetime
from parking_eindhoven import ParkingEindhoven
from database import connection, cursor

city = "Eindhoven"

async def async_get_locations(number):
    """Get parking data from API.

    Args:
        number: The number of parking lots to get.
    """
    async with ParkingEindhoven(parking_type=3) as client:
        locations = await client.locations(rows=number)
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
            # Define unique id
            location_id = uuid.uuid4().hex[:8]

            sql = """INSERT INTO `parking_cities` (`id`, `city`, `street`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (location_id, str(city), str(item.street), None, item.number, float(item.longitude), float(item.latitude), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f"{count} - Parkeerplaatsen gevonden")
        print(f'{city} - KLAAR met updaten van database')