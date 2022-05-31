import json, datetime, uuid

from database import connection, cursor

municipality = "Den Haag"

def upload():
    """Upload the data from the JSON file to the database."""

    den_haag_file = "data/parking-denhaag.json"
    den_haag_data = open(den_haag_file).read()
    den_haag_obj = json.loads(den_haag_data)
    try:
        for item in den_haag_obj["features"]:
            # Hark cordinaten binnen
            combined_coordinates = str(item["geometry"]["coordinates"])
            # Split cordinaten in X en Y
            longitude,latitude = combined_coordinates.split(',')
            # Voer replace uit om blok haken te verwijderen
            longitude = longitude.replace('[', '')
            latitude = latitude.replace(']', '')

            location_id = uuid.uuid4().hex[:8]
            item = item["properties"]

            sql = """INSERT INTO `parking_cities` (`id`, `country_id`, `province_id`, `municipality`, `street`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (location_id, int(157), int(9), str(municipality), str(item["ORIENTATIE"]), number(item["CAPACITEIT"]), float(longitude), float(latitude), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
            cursor.execute(sql, val)
        connection.commit()
    except Exception as e:
        print(f'MySQL error: {e}')
    finally:
        print(f'{municipality} - KLAAR met updaten van database')

def number(value):
    if value is None:
        return 1
    else:
        return value