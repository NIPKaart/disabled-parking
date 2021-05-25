import json, datetime, uuid

from pymysql import NULL

from database import connection, cursor

city = "Den Haag"

def upload():
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

            id = uuid.uuid4().hex[:8]

            sql = """INSERT INTO `parking_cities` (`id`, `city`, `orientation`, `number`, `longitude`, `latitude`, `visibility`, `created_at`, `updated_at`)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = (id, str(city), str(item["properties"]["ORIENTATIE"]), number(item["properties"]["CAPACITEIT"]), float(longitude), float(latitude), bool(True), (datetime.datetime.now()), (datetime.datetime.now()))
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

def number(value):
    if value is None:
        return 1
    else:
        return value

def update():
    return