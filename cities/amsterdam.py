import json, datetime, uuid, aiohttp

from shapely.geometry import Polygon
from database import connection, cursor

city = "Amsterdam"

async def async_get_locations():
    """Get the data from the GeoJSON API endpoint."""
    async with aiohttp.ClientSession() as client:
        async with client.get('https://api.data.amsterdam.nl/v1/parkeervakken/parkeervakken?eType=E6a&_format=geojson') as resp:
            return await resp.text()


def correct_orientation(type) -> str:
    """Correct the orientation of the parking lot."""
    if type == "Vissengraat":
        return str("Visgraat")
    return str(type)


def upload(data_set):
    """Upload the data from the JSON file to the database."""
    amsterdam_obj = json.loads(data_set)
    count: int
    try:
        for index, item in enumerate(amsterdam_obj["features"], 1):
            count = index

            # Get the coordinates of the parking lot with centroid
            P = Polygon(item["geometry"]["coordinates"][0])
            location_cords = P.centroid

            # Define unique id
            location_id = uuid.uuid4().hex[:8]
            item = item["properties"]

            sql = """INSERT INTO `parking_cities` (`id`, `city`, `street`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (location_id, str(city), str(item["straatnaam"]), correct_orientation(item["type"]), int(item["aantal"]), float(location_cords.x), float(location_cords.y), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f"{count} - Parkeerplaatsen gevonden")
        print(f'{city} - KLAAR met updaten van database')