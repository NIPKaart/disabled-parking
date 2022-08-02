"""Manage the location data of Groningen."""
import datetime
import json
import os
import urllib.request
from pathlib import Path

import pytz
from dotenv import load_dotenv

from app.database import connection, cursor
from app.helper import centroid

MUNICIPALITY = "Groningen"
GEOCODE = "NL-GR"
CBS_CODE = "0014"

load_dotenv()
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


def download():
    """Download the data as JSON file."""

    # Create a variable and pass the url of file to be downloaded
    url = f'{os.getenv("CKAN_SOURCE")}/dataset/7ff17203-0dba-40f8-9abf-1b770baa6be6/resource/822d72b7-7b83-43f6-8bd7-2c8c657693f5/download/gemeentegroningen_parkeervakken.geojson'
    # Copy a network object to a local file
    urllib.request.urlretrieve(url, "app/data/parking-groningen.json")
    print(f"{MUNICIPALITY} - KLAAR met downloaden")


def upload():
    """Upload the data from the JSON file to the database."""
    groningen_file = "app/data/parking-groningen.json"
    with open(groningen_file, "r", encoding="UTF-8") as groningen_data:
        groningen_obj = json.load(groningen_data)

    count: int = 0
    try:
        for item in groningen_obj["features"]:
            if item["properties"]["Vakfunctie"] == "Invaliden_alg":
                count += 1
                # Define unique id
                location_id = f"{GEOCODE}-{CBS_CODE}-{item['properties']['VakID']}"
                # Get the coordinates of the parking lot with centroid
                latitude, longitude = centroid(item["geometry"]["coordinates"])
                item = item["properties"]
                # Make the sql query
                sql = """INSERT INTO `parking_cities` (id, country_id, province_id, municipality, street, number, latitude, longitude, visibility, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY
                    UPDATE id=values(id),
                            country_id=values(country_id),
                            province_id=values(province_id),
                            municipality=values(municipality),
                            street=values(street),
                            number=values(number),
                            latitude=values(latitude),
                            longitude=values(longitude),
                            updated_at=values(updated_at)"""
                val = (
                    location_id,
                    int(157),
                    int(1),
                    str(MUNICIPALITY),
                    str(item["Straatnaam"]),
                    int(1),
                    float(latitude),
                    float(longitude),
                    bool(True),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                    (datetime.datetime.now(tz=pytz.timezone("Europe/Amsterdam"))),
                )
                cursor.execute(sql, val)
        connection.commit()
    except Exception as error:
        print(f"MySQL error: {error}")
    finally:
        print(f"{count} - Parkeerplaatsen gevonden")
        print(f"{MUNICIPALITY} - KLAAR met updaten van database")
