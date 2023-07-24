"""Setup database connection."""
import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv()
env_path = Path() / ".env"
load_dotenv(dotenv_path=env_path)

# MYSQL credentials
DB_SERVER = os.getenv("DB_SERVER")
DB_PORT = int(os.getenv("DB_PORT"))
DATABASE = os.getenv("DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Connect to MySQL
connection = pymysql.connect(
    host=DB_SERVER,
    port=DB_PORT,
    user=DB_USERNAME,
    password=DB_PASSWORD,
    database=DATABASE,
)
cursor = connection.cursor()


def truncate(city_name: str) -> None:
    """Remove all data from a city.

    Args:
    ----
        city_name: The name of the city, it's case sensitive!
    """
    try:
        sql = "DELETE FROM `parking_cities` WHERE `municipality`=%s"
        cursor.execute(sql, city_name)
        connection.commit()
    except pymysql.Error as error:
        print(f"MySQL error: {error}")
    finally:
        print(f"{city_name} - old data has been deleted")
