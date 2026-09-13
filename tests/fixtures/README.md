# One package-to-adapter example

`hamburg.json` contains only the first feature from [python-hamburg v3.0.0](https://github.com/klaasnicolaas/python-hamburg/blob/v3.0.0/tests/fixtures/disabled_parking.geojson), the locked package version. The surrounding response metadata and other records were removed. This sample checks that the installed parser feeds our mapping and CLI. It is not a complete dataset or an accepted pilot source; completeness is not inferred from it.

Mapping and writer tests otherwise construct small Python objects. Source parsing and pagination tests belong upstream. There is no fixture collection for all packages.

Fixture copyright: 2022–2023 Klaas Schoute. See the [MIT license](../../LICENSE).
