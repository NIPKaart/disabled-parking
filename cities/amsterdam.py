import json, datetime, uuid

from database import connection, cursor

city = "Amsterdam"

def upload():
    amsterdam_file = "data/parking-amsterdam.json"
    amsterdam_data = open(amsterdam_file).read()
    amsterdam_obj = json.loads(amsterdam_data)
    try:
        for item in amsterdam_obj["features"]:
            # Hark cordinaten binnen
            combined_coordinates = str(item["geometry"]["coordinates"])
            # Split cordinaten in X en Y
            longitude,latitude = combined_coordinates.split(',')
            # Voer replace uit om blok haken te verwijderen
            longitude = longitude.replace('[', '')
            latitude = latitude.replace(']', '')

            id = uuid.uuid4().hex[:8]

            sql = """INSERT INTO `parking_cities` (`id`, `city`, `street`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (id, str(city), str(item["properties"]["straatnaam"]), str(item["properties"]["type"]), int(item["properties"]["aantal"]), float(longitude), float(latitude), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
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