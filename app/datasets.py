"""Register deliverable datasets separately from source-specific HTTP clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from app.cities.belgium import namur
from app.cities.netherlands import amsterdam, eindhoven

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.records import Collection


class Source(Protocol):
    """Produce normalized records and explicit evidence of a complete selection."""

    async def collect(self) -> Collection:
        """Retrieve a complete selection or raise without delivering partial data."""


@dataclass(frozen=True)
class SourceDescription:
    """How core recognises, attributes and approves a dataset (core ADR 0013)."""

    name: str
    publisher: str
    source_url: str
    licence: str | None
    terms_url: str
    attribution: str
    country: str
    subdivision: str
    municipality_scheme: str
    municipality_code: str
    municipality_name: str
    bounds: tuple[float, float, float, float]
    expected_interval_hours: int

    def as_dict(self) -> dict[str, object]:
        """Return the `source` block sent in every delivery."""
        return {
            "name": self.name,
            "publisher": self.publisher,
            "source_url": self.source_url,
            "licence": self.licence,
            "terms_url": self.terms_url,
            "attribution": self.attribution,
            "area": {
                "country": self.country,
                "subdivision": self.subdivision,
                "municipality": {
                    "scheme": self.municipality_scheme,
                    "code": self.municipality_code,
                    "name": self.municipality_name,
                },
            },
            "bounds": list(self.bounds),
            "expected_interval_hours": self.expected_interval_hours,
        }


@dataclass(frozen=True)
class Dataset:
    """One delivery identity, selection and isolated collector state location."""

    code: str
    selection: str
    source: Callable[[], Source]
    description: SourceDescription


# Licences and terms verified on the publication pages on 2026-09-28.
DATASETS = {
    "amsterdam": Dataset(
        code="nl-amsterdam",
        selection="e6a-all",
        source=amsterdam.Municipality,
        description=SourceDescription(
            name="Amsterdam algemene gehandicaptenparkeerplaatsen",
            publisher="Gemeente Amsterdam",
            source_url="https://api.data.amsterdam.nl/v1/parkeervakken/parkeervakken/",
            licence="CC0-1.0",
            terms_url="https://data.overheid.nl/dataset/318a98b8-ef87-4335-9674-f5405f2bc4be",
            attribution=(
                "Gemeente Amsterdam; parkeervakken E6a; capaciteit is een schatting."
            ),
            country="NL",
            subdivision="NL-NH",
            municipality_scheme="nl-cbs",
            municipality_code="GM0363",
            municipality_name="Amsterdam",
            bounds=(4.65, 52.2, 5.15, 52.5),
            expected_interval_hours=24,
        ),
    ),
    "eindhoven": Dataset(
        code="nl-eindhoven",
        selection="gehandicapten-all",
        source=eindhoven.Municipality,
        # The source says public domain but identifies no verified SPDX licence.
        description=SourceDescription(
            name="Eindhoven gehandicaptenparkeerplaatsen",
            publisher="Gemeente Eindhoven",
            source_url="https://data.eindhoven.nl/explore/dataset/parkeerplaatsen/",
            licence=None,
            terms_url="https://data.eindhoven.nl/explore/dataset/parkeerplaatsen/information/",
            attribution=(
                "Gemeente Eindhoven; parkeerplaatsen, type Parkeerplaats Gehandicapten."
            ),
            country="NL",
            subdivision="NL-NB",
            municipality_scheme="nl-cbs",
            municipality_code="GM0772",
            municipality_name="Eindhoven",
            bounds=(5.32, 51.35, 5.62, 51.52),
            expected_interval_hours=24,
        ),
    ),
    "namur": Dataset(
        code="be-namur",
        selection="pmr-all",
        source=namur.Municipality,
        # Source licence, official PMR selection and INS code checked 2026-10-07.
        description=SourceDescription(
            name="Namur stationnement PMR en voirie",
            publisher="Ville de Namur",
            source_url="https://data.namur.be/explore/dataset/namur-parking-emplacements/",
            licence="CC-BY-4.0",
            terms_url="https://data.namur.be/terms/terms-and-conditions/",
            attribution=(
                "Ville de Namur; Namur - Parking - Emplacements (points); "
                "sélection PMR, normalisée par NIPKaart; "
                "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). "
                "Couverture de l'agglomération; liste indicative, "
                "la signalisation sur place fait foi."
            ),
            country="BE",
            subdivision="BE-WNA",
            municipality_scheme="be-ins",
            municipality_code="92094",
            municipality_name="Namur",
            bounds=(4.70, 50.35, 5.05, 50.60),
            expected_interval_hours=24,
        ),
    ),
}
