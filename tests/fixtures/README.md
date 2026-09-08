# Fixture provenance

These are up to the first two rows of the upstream fixtures at the package versions in `uv.lock`. Response metadata is retained, so these reduced samples must never be treated as complete datasets. They are parser and mapping examples, not live source or licensing acceptance. Eindhoven contains generic parking examples; classification for a production disabled-parking fetch still requires validation.

| Fixture | Upstream fixture | Package version |
| --- | --- | --- |
| `antwerpen.json` | [klaasnicolaas/python-antwerpen/disabled_parking.geojson](https://github.com/klaasnicolaas/python-antwerpen/blob/v1.1.0/tests/fixtures/disabled_parking.geojson) | 1.1.0 |
| `arnhem.json` | [klaasnicolaas/python-arnhem/e6a_parking.json](https://github.com/klaasnicolaas/python-arnhem/blob/v0.1.1/tests/fixtures/e6a_parking.json) | 0.1.1 |
| `brussel.json` | [klaasnicolaas/python-brussel/disabled_parkings.json](https://github.com/klaasnicolaas/python-brussel/blob/v0.2.2/tests/fixtures/disabled_parkings.json) | 0.2.2 |
| `dresden.json` | [klaasnicolaas/python-dresden/disabled_parking.geojson](https://github.com/klaasnicolaas/python-dresden/blob/v0.2.1/tests/fixtures/disabled_parking.geojson) | 0.2.1 |
| `dusseldorf.json` | [klaasnicolaas/python-dusseldorf/disabled_parkings.json](https://github.com/klaasnicolaas/python-dusseldorf/blob/v1.0.0/tests/fixtures/disabled_parkings.json) | 1.0.0 |
| `eindhoven.json` | [klaasnicolaas/python-eindhoven/parking.json](https://github.com/klaasnicolaas/python-eindhoven/blob/v4.0.0/tests/fixtures/parking.json) | 4.0.0 |
| `hamburg.json` | [klaasnicolaas/python-hamburg/disabled_parking.geojson](https://github.com/klaasnicolaas/python-hamburg/blob/v3.0.0/tests/fixtures/disabled_parking.geojson) | 3.0.0 |
| `koeln.json` | [klaasnicolaas/python-koeln/disabled_parkings.json](https://github.com/klaasnicolaas/python-koeln/blob/v0.3.1/tests/fixtures/disabled_parkings.json) | 0.3.1 |
| `liege.json` | [klaasnicolaas/python-liege/disabled_parkings.json](https://github.com/klaasnicolaas/python-liege/blob/v1.0.0/tests/fixtures/disabled_parkings.json) | 1.0.0 |
| `namur.json` | [klaasnicolaas/python-namur/parking_pmr.json](https://github.com/klaasnicolaas/python-namur/blob/v1.0.0/tests/fixtures/parking_pmr.json) | 1.0.0 |
| `amsterdam.json` | [klaasnicolaas/python-odp-amsterdam/parking.json](https://github.com/klaasnicolaas/python-odp-amsterdam/blob/v6.1.2/tests/fixtures/parking.json) | 6.1.2 |

Upstream MIT license notices are preserved in `licenses/`. The four direct-JSON municipalities use explicitly synthetic rows in the tests, based on the field names already consumed by their adapters.
