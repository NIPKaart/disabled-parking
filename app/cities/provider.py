"""Select the existing municipal adapters without opening a database."""
# Copyright (c) 2026 NIPKaart

from app.cities.belgium import antwerpen, brussel, liege, namur
from app.cities.germany import dresden, dusseldorf, hamburg, koeln
from app.cities.netherlands import (
    amersfoort,
    amsterdam,
    arnhem,
    den_haag,
    eindhoven,
    groningen,
    zoetermeer,
)


class CityProvider:
    """Class to provide the correct city."""

    def provide_city(self, city_name: str) -> object:  # noqa: C901, PLR0912
        """Provide the correct city.

        Args:
        ----
            city_name (str): The city to provide.

        Returns:
        -------
            city_class (class): The class of the city.

        """
        match city_name:
            case "antwerpen":
                city_class = antwerpen.Municipality()
            case "amersfoort":
                city_class = amersfoort.Municipality()
            case "amsterdam":
                city_class = amsterdam.Municipality()
            case "arnhem":
                city_class = arnhem.Municipality()
            case "brussel":
                city_class = brussel.Municipality()
            case "den haag":
                city_class = den_haag.Municipality()
            case "dusseldorf":
                city_class = dusseldorf.Municipality()
            case "dresden":
                city_class = dresden.Municipality()
            case "eindhoven":
                city_class = eindhoven.Municipality()
            case "groningen":
                city_class = groningen.Municipality()
            case "hamburg":
                city_class = hamburg.Municipality()
            case "koeln":
                city_class = koeln.Municipality()
            case "liege":
                city_class = liege.Municipality()
            case "namur":
                city_class = namur.Municipality()
            case "zoetermeer":
                city_class = zoetermeer.Municipality()
            case _:
                msg = f"{city_name} is not a valid city."
                raise ValueError(msg)
        return city_class
