import json, datetime, uuid, os
import urllib.request

from database import connection, cursor
from dotenv import load_dotenv
from pathlib import Path

municipality = "Zoetermeer"

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

def download():
    """Download the data as JSON file."""

    # Create a variable and pass the url of file to be downloaded
    url = f'{os.getenv("SOURCE")}/308bb3581ba646afad6f776a8f7e4e67_0.geojson'
    # Copy a network object to a local file
    urllib.request.urlretrieve(url, 'data/parking-zoetermeer.json')
    print(f'{municipality} - KLAAR met downloaden')

def upload():
    """Upload the data from the JSON file to the database."""

    zoetermeer_file = "data/parking-zoetermeer.json"
    zoetermeer_data = open(zoetermeer_file).read()
    zoetermeer_obj = json.loads(zoetermeer_data)
    try:
        for item in zoetermeer_obj["features"]:
            location_id = uuid.uuid4().hex[:8]

            sql = """INSERT INTO `parking_cities` (`id`, `country_id`, `province_id`, `municipality`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (location_id, int(157), int(9), str(municipality), int(item["properties"]["plaatsen"]), float(item["properties"]["lon"]), float(item["properties"]["lat"]), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f'{municipality} - KLAAR met updaten van database')

def update():
    return