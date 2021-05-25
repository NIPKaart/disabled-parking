import json, datetime, uuid, os
import urllib.request

from database import connection, cursor
from dotenv import load_dotenv
from pathlib import Path

city = "Zoetermeer"

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

def download():
    # Create a variable and pass the url of file to be downloaded
    url = f'{os.getenv("SOURCE")}/77cd514505dd40589f52f99d0e5edd6a_0.geojson'
    # Copy a network object to a local file
    urllib.request.urlretrieve(url, r'data/parking-zoetermeer.json')
    print(f'{city} - KLAAR met downloaden')

def upload():
    zoetermeer_file = "data/parking-zoetermeer.json"
    zoetermeer_data = open(zoetermeer_file).read()
    zoetermeer_obj = json.loads(zoetermeer_data)
    try:
        for item in zoetermeer_obj["features"]:
            id = uuid.uuid4().hex[:8]

            sql = """INSERT INTO `parking_cities` (`id`, `city`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (id, str(city), int(item["properties"]["plaatsen"]), float(item["properties"]["lon"]), float(item["properties"]["lat"]), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f'{city} - KLAAR met updaten van database')

def truncate():
    try:
        sql = "DELETE FROM `parking_cities` WHERE `city`=%s"
        cursor.execute(sql, city)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f'{city} - verwijderen van de data')

def update():
    return