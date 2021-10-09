import uuid, parking_eindhoven, datetime, aiohttp

from database import connection, cursor

city = "Eindhoven"

async def async_get_locations(number, type):
    """Get parking data from API."""

    async with aiohttp.ClientSession() as client:
        return await parking_eindhoven.get_locations(number, type, client)

def upload(data_set):
    """Upload the data_set to the database."""

    try:
        for item in data_set:
            id = uuid.uuid4().hex[:8]
            sql = """INSERT INTO `parking_cities` (`id`, `city`, `street`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (id, str(city), str(item.street), None, item.number, float(item.longitude), float(item.latitude), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f'{city} - KLAAR met updaten van database')

def update():
    return