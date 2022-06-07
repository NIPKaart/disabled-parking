import json, datetime, aiohttp, pytz
from database import connection, cursor

municipality = "Amsterdam"
cbs_code = "0363"

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


def centroid(vertexes):
    """Calculate the centroid of a polygon.

    Args:
        vertexes (list): A list of points.

    Returns:
        Point: The centroid of the polygon.
    """
    _x_list = [vertex [0] for vertex in vertexes[0]]
    _y_list = [vertex [1] for vertex in vertexes[0]]

    _len = len(vertexes[0])
    _x = sum(_x_list) / _len
    _y = sum(_y_list) / _len
    return(_y, _x)


def upload(data_set):
    """Upload the data from the JSON file to the database."""
    amsterdam_obj = json.loads(data_set)
    count: int
    try:
        for index, item in enumerate(amsterdam_obj["features"], 1):
            count = index

            # Get the coordinates of the parking lot with centroid
            latitude, longitude = centroid(item["geometry"]["coordinates"])
            # Define unique id
            location_id = f"{cbs_code}-{item['id'].split('.')[1]}"

            item = item["properties"]
            # Make the sql query
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
            val = (location_id, int(157), int(8), str(municipality), str(item["straatnaam"]), correct_orientation(item["type"]),
                   int(item["aantal"]), float(longitude), float(latitude), bool(True), (datetime.datetime.now(tz=pytz.timezone('Europe/Amsterdam'))),
                   (datetime.datetime.now(tz=pytz.timezone('Europe/Amsterdam'))))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f"{count} - Parkeerplaatsen gevonden")
        print(f'{municipality} - KLAAR met updaten van database')