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

## About

This project makes it possible to download and upload parking data from municipalities to the [NIPkaart][nipkaart] platform. If the data is regularly updated, it is possible to automate this with a docker container.

## Supported cities

These are the cities currently supported:

| Country | City | Locations | Update frequency | Crontab |
|:--------|:-----|:----------|:-----------------| :-------|
| Belgium | Antwerpen | 1664 |  |
| Belgium | Brussel | 877 |  |
| Belgium | Liege | 952 |  |
| Belgium | Namur | 305 |  |
| Germany | Dresden | 477 |  |
| Germany | Dusseldorf | 327 |  |
| Germany | Hamburg | 812 (says 813) |  |
| Germany | Köln / Cologne | 441 |  |
| Netherlands | Amersfoort | 149 | every monday at 03:00 | `0 3 * * 1` |
| Netherlands | Amsterdam | 1328 | every second day of the month at 03:00 | `0 3 2 * *` |
| Netherlands | Arnhem | 88 |  |
| Netherlands | Den Haag | 234 (says 241) | every second day of the month at 02:30 | `30 2 2 * *` |
| Netherlands | Eindhoven | 180 | every second day of the month at 03:00 | `0 3 2 * *` |
| Netherlands | Groningen | 173 |  |
| Netherlands | Zoetermeer | 388 |  |


## Development

This Python project is fully managed using the [Poetry][poetry] dependency
manager.

You need at least:

- Python 3.11+
- [Poetry][poetry-install]

1. Create a `.env` file
```bash
cp .env.example .env
```
2. Fillout the database credentials and which city you want to upload

3. Install all packages, including all development requirements:

```bash
poetry install
```

Poetry creates by default an virtual environment where it installs all
necessary pip packages, to enter or exit the venv run the following commands:

```bash
poetry shell
exit
```

Setup the pre-commit check, you must run this inside the virtual environment:

```bash
pre-commit install
```

*Now you're all set to get started!*

As this repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run pre-commit run --all-files
```

<details>
  <summary>Click here to see more!</summary>

### Build image

```bash
docker build -t parking-[CITY] .
```

### Run the image

```bash
docker run parking-[CITY] -d --restart on-failure --name nipkaart-parking-[CITY]
```

or

```bash
docker stack deploy -c deploy/[CITY].yml parking
```

### Crontab

Certain datasets are regularly updated, so that we can update them automatically in the NIPKaart database.

`0 3 1 * *` = Run every first day of the month at 03:00<br>
`30 2 2 * *` = Run every second day of the month at 02:30<br>
`0 3 2 * *` = Run every second day of the month at 03:00<br>
`0 3 * * 1` = Run every monday at 03:00<br>
`30 2 * * 1` = Run every monday at 02:30<br>
`0 3 * * 2` = Run every thuesday at 03:00<br>
`*/2 * * * *` = Run every 2 minutes<br>

Crontab generator: https://crontab.guru

### Geocode

The value you should use for this purpose can be obtained from the [ISO 3166-2 standard](https://en.wikipedia.org/wiki/ISO_3166-2). This code represents a province or state within a specific country. It helps differentiate data sets for the same area when multiple datasets are combined.

### SQL query

Below are the values that NIPKaart expects to get:

| value | required? | description |
|:------|:----------|:------------|
| `id` | yes | The ID of the parking location |
| `country_id` | yes | The country ID determined by NIPKaart |
| `province_id` | yes | The province ID determined by NIPKaart |
| `municipality` | yes | The municipality name |
| `street` | no | The street name |
| `orientation` | no | The orientation of the parking location |
| `number` | yes | The number of parking spots on that location |
| `longitude` | yes | The longitude of the parking location |
| `latitude` | yes | The latitude of the parking location |
| `visibility` | yes | The visibility of the parking location |
| `created_at` | yes | The date and time of the creation of the parking location |
| `updated_at` | yes | The date and time of the last update of the parking location |

</details>

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

[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com
