"""Scrape and upload parking data to NIPKaart system"""
import cities.zoetermeer as zoetermeer
import cities.arnhem as arnhem
import cities.den_haag as den_haag
import cities.amsterdam as amsterdam
import database as database
import asyncio

if __name__ == '__main__':
    print("--- Start program ---")
    """ Zoetermeer """
    # zoetermeer.download()
    # zoetermeer.upload()
    # zoetermeer.truncate()

    # arnhem.download()
    """ Amsterdam """
    # amsterdam.upload()

    """ Den Haag """
    # den_haag.upload()