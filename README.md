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

## Status: small export example, awaiting pilot selection

This draft retains only the Hamburg mapping as an example from the earlier experiment. **Hamburg has not been accepted as the live pilot.** All other municipality source-fetch methods remain available; they are not migrated to a new export interface here. Source choice and actual live fetching belong to [core#1214](https://github.com/NIPKaart/core/issues/1214) and [#774](https://github.com/NIPKaart/disabled-parking/issues/774).

The target is package → adapter → private bucket → core. This example only demonstrates package parsing → mapping → local file. The bucket implementation and core intake are not built. See [the canonical plan](https://github.com/NIPKaart/core/issues/1176).

## Run the example

```bash
uv sync --locked
uv run --locked python export.py --city hamburg --input tests/fixtures/hamburg.json --output /tmp/hamburg.json
uv run --locked python -m unittest discover -s tests -v
uv run --locked pre-commit run --all-files
```

Only `hamburg` is supported by the example CLI. No source request, database credentials or cloud account is required. The response sample contains one feature; [its attribution](tests/fixtures/README.md) is retained in one place. All other tests use small Python objects, not copied upstream fixtures.

The file retains full source IDs, nullable capacity and available restrictions. Invalid/duplicate records or the 10,000-record / 32 MiB operational limits fail the export; an existing output file is replaced only after successful writing. The experimental envelope reports unknown retrieval time and completeness, and is not a valid complete live delivery.

## Required replacement before pilot acceptance

Issue #774 must connect the selected live source, replace `municipal-records-draft` and unconditional null live metadata with the format consumed by core, and remove superseded code/tests/instructions in the same change. This reference must be reduced to the selected source or discarded if it does not fit; it creates no requirement to adopt its abstraction or retain a compatibility layer. Local replay can remain useful using the same accepted format.

## Container

```bash
docker build -t disabled-parking .
docker run --rm --network none disabled-parking --city hamburg --input /app/tests/fixtures/hamburg.json --output /tmp/hamburg.json
```

The container runs once and exits; without arguments it shows help. Output in this disposable example container is discarded. Mount a writable output directory to retain it. The old SQL/cron runtime is removed.

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
