"""General class for cities."""


class City:
    """General class for cities."""

    def __init__(self, name, country, country_id, province_id, geo_code):
        """Initialize the class."""
        self.name = name
        self.country = country
        self.country_id = country_id
        self.province_id = province_id
        self.geo_code = geo_code
