"""Register deliverable datasets separately from source-specific HTTP clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from app.cities.belgium import antwerpen, namur
from app.cities.netherlands import amsterdam, arnhem, den_haag, eindhoven, groningen
from app.cities.sweden import stockholm

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
    "antwerpen": Dataset(
        code="be-antwerpen",
        selection="identified-disabled-all",
        source=antwerpen.Municipality,
        # Layer, source claims and reuse terms checked on 2026-10-13.
        description=SourceDescription(
            name="Antwerpen parkeerplaatsen voor personen met een handicap",
            publisher="Stad Antwerpen",
            source_url="https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek6/MapServer/585",
            licence=None,
            terms_url="https://www.antwerpen.be/info/gratis-open-data-licentie",
            attribution=(
                "bron stad Antwerpen; parkeerplaatsen voor personen met een handicap; "
                "Gratis Open Data Licentie Vlaanderen v. 1.0; "
                "genormaliseerd door NIPKaart. Alleen records met GISID. "
                "Broninventarisatie betaald parkeerareaal; geen gemeentebrede dekking. "
                "Toegang en venstertijden behouden; bebording ter plaatse is leidend."
            ),
            country="BE",
            subdivision="BE-VAN",
            municipality_scheme="be-ins",
            municipality_code="11002",
            municipality_name="Antwerpen",
            bounds=(4.25, 51.10, 4.60, 51.40),
            expected_interval_hours=24,
        ),
    ),
    "groningen": Dataset(
        code="nl-groningen",
        selection="gehandicapten-algemeen-e06-all",
        source=groningen.Municipality,
        # Publisher, licence and monthly source revision checked 2026-10-13.
        description=SourceDescription(
            name="Groningen algemene gehandicaptenparkeervakken",
            publisher="Gemeente Groningen",
            source_url="https://data.groningen.nl/dataset/parkeervakken-gemeente-groningen",
            licence="CC-BY-4.0",
            terms_url="https://data.groningen.nl/dataset/parkeervakken-gemeente-groningen",
            attribution=(
                "Gemeente Groningen; Parkeervakken gemeente Groningen; "
                "TYPE=gehandicapten algemeen en ETYPE=E06; "
                "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); "
                "genormaliseerd door NIPKaart. Dekking volgens bron: schilwijken. "
                "Bron-ID's wisselen; core beoordeelt locatiekoppelingen. "
                "Bebording ter plaatse is leidend."
            ),
            country="NL",
            subdivision="NL-GR",
            municipality_scheme="nl-cbs",
            municipality_code="GM0014",
            municipality_name="Groningen",
            bounds=(6.40, 53.05, 6.85, 53.45),
            expected_interval_hours=24,
        ),
    ),
    "den-haag": Dataset(
        code="nl-den-haag",
        selection="algemeen-wfs-all",
        source=den_haag.Municipality,
        # Official map WFS and access constraints checked on 2026-10-13.
        description=SourceDescription(
            name="Den Haag algemene gehandicaptenparkeerplaatsen",
            publisher="Gemeente Den Haag",
            source_url=(
                f"{den_haag.SOURCE_URL}?service=WFS&version=2.0.0&request=GetFeature"
                f"&typeName={den_haag.FEATURE_TYPE}&outputFormat=application/json"
            ),
            licence=None,
            terms_url=(
                f"{den_haag.SOURCE_URL}?service=WFS&version=2.0.0"
                "&request=GetCapabilities"
            ),
            attribution=(
                "Gemeente Den Haag; algemene gehandicaptenparkeerplaatsen, "
                "gemeentelijke centroiden; genormaliseerd door NIPKaart. "
                "Werkingstijden en beperkingen behouden in bronclaims; "
                "bebording ter plaatse is leidend."
            ),
            country="NL",
            subdivision="NL-ZH",
            municipality_scheme="nl-cbs",
            municipality_code="GM0518",
            municipality_name="'s-Gravenhage",
            bounds=(4.20, 52.00, 4.43, 52.13),
            expected_interval_hours=24,
        ),
    ),
    "stockholm": Dataset(
        code="se-stockholm",
        selection="prorelsehindrad-all",
        source=stockholm.Municipality,
        description=SourceDescription(
            name="Stockholm parkeringsföreskrifter för rörelsehindrade",
            publisher="Stockholms stad, Trafikkontoret",
            source_url="https://openparking.stockholm.se/LTF-Tolken/v1/prorelsehindrad/all",
            licence=None,
            terms_url="https://openstreetws.stockholm.se/home/",
            attribution=(
                "Stockholms stad, Trafikkontoret; prorelsehindrad. "
                "Lokala trafikföreskrifter, inte enskilt verifierade "
                "parkeringsplatser. "
                "Skyltningen på plats gäller; giltighet och villkor bevaras i källdata."
            ),
            country="SE",
            subdivision="SE-AB",
            municipality_scheme="se-scb",
            municipality_code="0180",
            municipality_name="Stockholm",
            bounds=(17.70, 59.20, 18.30, 59.50),
            expected_interval_hours=24,
        ),
    ),
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
    "arnhem": Dataset(
        code="nl-arnhem",
        selection="e6a-all",
        source=arnhem.Municipality,
        # Publisher, licence and daily cadence checked on 2026-10-07.
        description=SourceDescription(
            name="Arnhem gehandicaptenparkeervakken E6a",
            publisher="Gemeente Arnhem",
            source_url="https://geo.arnhem.nl/arcgis/rest/services/OpenData/Parkeervakken/MapServer/0",
            licence="CC-BY-4.0",
            terms_url="https://data.overheid.nl/dataset/parkeervakken-arnhem",
            attribution=(
                "Gemeente Arnhem; Parkeervakken, selectie RVV_SOORT=E6a; "
                "genormaliseerd door NIPKaart; "
                "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). "
                "Aanvullende bordtekst behouden; bebording ter plaatse is leidend."
            ),
            country="NL",
            subdivision="NL-GE",
            municipality_scheme="nl-cbs",
            municipality_code="GM0202",
            municipality_name="Arnhem",
            bounds=(5.80, 51.93, 6.02, 52.09),
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
