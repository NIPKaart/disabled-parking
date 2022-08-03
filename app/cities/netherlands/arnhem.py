"""Manage the location data of Arnhem."""
import datetime
import json
import os
import urllib.request
from pathlib import Path

import pytz
from dotenv import load_dotenv

from app.database import connection, cursor

MUNICIPALITY = "Arnhem"
GEOCODE = "NL-GE"
CBS_CODE = "0202"

load_dotenv()
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


def download():
    """Download the data as JSON file."""

    # Create a variable and pass the url of file to be downloaded
    url = f'{os.getenv("ARCGIS_SOURCE")}/6f301547133a4acda9074ec3ca9b075b_0.geojson'
    # Copy a network object to a local file
    urllib.request.urlretrieve(url, "app/data/parking-arnhem.json")
    print(f"{MUNICIPALITY} - KLAAR met downloaden")


def upload():
    """Upload the data from the JSON file to the database."""

    arnhem_file = "app/data/parking-arnhem.json"
    with open(arnhem_file, "r", encoding="UTF-8") as arnhem_data:
        arnhem_obj = json.load(arnhem_data)

    index: int
    try:
        for index, item in enumerate(arnhem_obj["features"], 1):
            item = item["properties"]
            # Generate unique id
            location_id = f"{GEOCODE}-{CBS_CODE}-{item['OBJECTID']}"

            sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, orientation, number, longitude, latitude, visibility, created_at, updated_at)
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
            val = (
                location_id,
                int(157),
                int(6),
                str(MUNICIPALITY),
                str(item["LOCATIE"]),
                str(item["TYPE_VAK"]),
                int(item["AANTAL"]),
                float(item["LON"]),
                float(item["LAT"]),
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
