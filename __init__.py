"""Scrape and upload parking data to NIPKaart system"""
import cities.zoetermeer as zoetermeer
import cities.arnhem as arnhem
import cities.den_haag as den_haag
import cities.amsterdam as amsterdam
import cities.eindhoven as eindhoven

import database as database
import asyncio

if __name__ == '__main__':
    print("--- Start program ---")
    """ Zoetermeer """
    # zoetermeer.download()
    # zoetermeer.upload()

    """ Arnhem """
    # arnhem.download()
    # arnhem.upload()

    """ Amsterdam """
    data_set = asyncio.run(amsterdam.async_get_locations())
    if (bool(data_set)):
        print("Data is opgehaald")
        database.truncate("Amsterdam")
        amsterdam.upload(data_set)

    """ Den Haag """
    # den_haag.upload()

    """ Eindhoven """
    # data_set = asyncio.run(eindhoven.async_get_locations(200, "Parkeerplaats Gehandicapten"))
    # print(data_set)
    # eindhoven.upload(data_set)

    # Database
    # database.truncate("Eindhoven")
