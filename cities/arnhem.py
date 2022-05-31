import json, datetime, uuid, os
import urllib.request

from database import connection, cursor
from dotenv import load_dotenv
from pathlib import Path

municipality = "Arnhem"

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

def download():
    """Download the data as JSON file."""

    # Create a variable and pass the url of file to be downloaded
    url = f'{os.getenv("SOURCE")}/6f301547133a4acda9074ec3ca9b075b_0.geojson'
    # Copy a network object to a local file
    urllib.request.urlretrieve(url, 'data/parking-arnhem.json')
    print(f'{municipality} - KLAAR met downloaden')

def upload():
    """Upload the data from the JSON file to the database."""

    arnhem_file = "data/parking-arnhem.json"
    arnhem_data = open(arnhem_file).read()
    arnhem_obj = json.loads(arnhem_data)
    try:
        for item in arnhem_obj["features"]:
            location_id = uuid.uuid4().hex[:8]
            item = item["properties"]

            sql= """INSERT INTO `parking_cities` (`id`, `country_id`, `province_id`, `municipality`, `street`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (location_id, int(157), int(6), str(municipality), str(item["LOCATIE"]), str(item["TYPE_VAK"]), int(item["AANTAL"]), float(item["LON"]), float(item["LAT"]), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f'{municipality} - KLAAR met updaten van database')