"""General class for cities."""


class City:
    """General class for cities."""

    def __init__(self, name, country, geo_code, cbs_code, limit):
        """Initialize the class."""
        self.name = name
        self.country = country
        self.geo_code = geo_code
        self.cbs_code = cbs_code
        self.limit = limit
