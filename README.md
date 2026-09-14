<!--
*** To avoid retyping too much info. Do a search and replace for the following:
*** github_username, repo_name
-->

<!-- Banner -->
![alt Banner of the disabled parking project](assets/banner_disabled_parking.png)

<!-- PROJECT SHIELDS -->
[![GitHub Activity][commits-shield]][commits]
[![GitHub Last Commit][last-commit-shield]][commits]
[![Linting][linting-shield]][linting-url]

![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)
[![Contributors][contributors-shield]][contributors-url]

[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

## Amsterdam export

Fetch the complete Amsterdam `E6a` selection through `odp-amsterdam` and write one local JSON file for core review:

```bash
uv sync --locked
uv run python export.py --city amsterdam --output /tmp/amsterdam.json
uv run python -m unittest discover -s tests -v
uv run pre-commit run --all-files
```

Python 3.12 or newer is required. The command needs network access, runs once and exits. It supports Amsterdam only; other municipalities retain their existing source-fetch methods.

The `nipkaart-municipal-pilot-1` document identifies dataset `nl-amsterdam-parkeervakken-e6a`, selection `e6a-all`, a delivery UUID, UTC retrieval-start time and the verified source count. Records retain full source IDs, Polygon rings, nullable estimated capacity, every regime and dataset validity dates. Core derives display points and reviews publication; general accessible parking does not mean unrestricted or currently available parking.

Incomplete/empty responses, duplicate IDs, unexpected personal reservations, invalid mappings or exceeded limits fail without replacing the last good file. Limits are 10,000 records, 32 MiB per file, 180 seconds for fetching and 100 rings / 10,000 positions per polygon. Core validates polygon topology using PostGIS. Run only one collection per dataset at a time; retry delivery using the same saved file.

The first handoff is this local file to [core#1215](https://github.com/NIPKaart/core/issues/1215). Later, [#775](https://github.com/NIPKaart/disabled-parking/issues/775) uploads the same format to a private bucket. No core database/API credentials, automatic publication or cloud transport are included here. See the [pilot source evidence](https://github.com/NIPKaart/core/blob/b068570/docs/development/data-import-pilot.md) and [file agreement](https://github.com/NIPKaart/core/blob/b068570/docs/development/data-import-contract.md). The government catalogue identifies the dataset as CC0; recheck the current API license before public use. The source announces future API-key requirements.

CI uses small package objects without live source requests. A separate live probe establishes source availability at that time, not an atomic snapshot or complete coverage of real-world parking.

## Container

```bash
docker build -t disabled-parking .
mkdir -p output
docker run --rm -v "$PWD/output:/output" disabled-parking --city amsterdam --output /output/amsterdam.json
```

The container runs once and exits; without arguments it shows help. The mounted directory retains the completed file.

## Contributing

Would you like to contribute to the development of this project? Then read the prepared [contribution guidelines](CONTRIBUTING.md) and go ahead!

Thank you for being involved! :heart_eyes:

## License

MIT License

Copyright (c) 2021-2024 Klaas Schoute

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[nipkaart]: https://nipkaart.nl

<!-- MARKDOWN LINKS & IMAGES -->
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[contributors-shield]: https://img.shields.io/github/contributors/nipkaart/disabled-parking.svg
[contributors-url]: https://github.com/nipkaart/disabled-parking/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/nipkaart/disabled-parking.svg
[forks-url]: https://github.com/nipkaart/disabled-parking/network/members
[stars-shield]: https://img.shields.io/github/stars/nipkaart/disabled-parking.svg
[stars-url]: https://github.com/nipkaart/disabled-parking/stargazers
[issues-shield]: https://img.shields.io/github/issues/nipkaart/disabled-parking.svg
[issues-url]: https://github.com/nipkaart/disabled-parking/issues
[license-shield]: https://img.shields.io/github/license/nipkaart/disabled-parking.svg
[commits-shield]: https://img.shields.io/github/commit-activity/y/nipkaart/disabled-parking.svg
[commits]: https://github.com/nipkaart/disabled-parking/commits/main
[last-commit-shield]: https://img.shields.io/github/last-commit/nipkaart/disabled-parking.svg
[linting-shield]: https://github.com/nipkaart/disabled-parking/actions/workflows/linting.yaml/badge.svg
[linting-url]: https://github.com/nipkaart/disabled-parking/actions/workflows/linting.yaml

[pre-commit]: https://pre-commit.com
