import json, datetime, os, aiohttp
import urllib.request

from database import connection, cursor
from dotenv import load_dotenv
from pathlib import Path

municipality = "Amersfoort"
cbs_code = "0307"

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

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


async def async_get_locations():
    """Get the data from the GeoJSON API endpoint."""
    async with aiohttp.ClientSession() as client:
        async with client.get(f'{os.getenv("CKAN_SOURCE")}/download/amersfoort-gehandicaptenparkeerplaatsen.json') as resp:
            return await resp.text()


def download():
    """Download the data as JSON file."""

    # Create a variable and pass the url of file to be downloaded
    url = f'{os.getenv("CKAN_SOURCE")}/download/amersfoort-gehandicaptenparkeerplaatsen.json'
    # Copy a network object to a local file
    urllib.request.urlretrieve(url, 'data/parking-amersfoort.json')
    print(f'{municipality} - KLAAR met downloaden')


def upload(data_set):
    """Upload the data from the JSON file to the database."""
    amersfoort_obj = json.loads(data_set)
    count: int
    try:
        for index, item in enumerate(amersfoort_obj["features"], 1):
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
            val = (location_id, int(157), int(7), str(municipality), str(item["STRAATNAAM"]), None, int(item["AANTAL_PLAATSEN"]), float(longitude), float(latitude), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f"{count} - Parkeerplaatsen gevonden")
        print(f'{municipality} - KLAAR met updaten van database')