"""General class for cities."""


class City:
    """General class for cities."""

    def __init__(
        self,
        name: str,
        country: str,
        geo_code: str,
    ) -> None:
        """Initialize the class."""
        self.name = name
        self.country = country
        self.geo_code = geo_code

    @property
    def source_id(self) -> str:
        """Reuse the existing geographic prefix without database primary keys."""
        code = getattr(self, "cbs_code", None) or getattr(self, "phone_code", None)
        if code is None:
            raise ValueError(self.name)
        return f"{self.geo_code}-{code}"
