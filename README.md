<!-- Banner -->
![alt Banner of the disabled parking project](assets/banner_disabled_parking.png)

<!-- PROJECT SHIELDS -->
[![GitHub Activity][commits-shield]][commits]
[![GitHub Last Commit][last-commit-shield]][commits]
[![Linting][linting-shield]][linting-url]

[![License][license-shield]](LICENSE)
[![Contributors][contributors-shield]][contributors-url]

[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

Collect municipal accessible-parking data for [NIPKaart](https://nipkaart.nl). One container collects Amsterdam (`nl-amsterdam`), Eindhoven (`nl-eindhoven`) and Namur (`be-namur`) and uploads complete deliveries to private Cloudflare R2 for review in core.

## Run

Copy `.env.example` to `.env`, fill in the private R2 bucket endpoint and credentials, then start:

```bash
chmod 600 .env
docker compose up -d --build
docker compose logs --tail 100 -f collector
```

Each dataset runs daily and retries failures independently. Set `COLLECTOR_INTERVAL_SECONDS` to change the interval. Keep the data volume during updates: **do not use `docker compose down -v`**, which deletes pending deliveries.

## Local export

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/). No R2 credentials needed.

```bash
uv sync --locked
uv run python export.py --city amsterdam --output /tmp/amsterdam.json
uv run python export.py --city eindhoven --output /tmp/eindhoven.json
uv run python export.py --city namur --output /tmp/namur.json
```

Exports are for source review; publication requires approval in core. See the [collector documentation](docs/collector.md) for source selections and limitations.

## Development

Register datasets in [`app/datasets.py`](app/datasets.py). Each source returns a shared `Collection`; the exporter and scheduler use the registry automatically.

```bash
uv run python -m unittest discover -s tests -v
uv run pre-commit run --all-files
```

See the [collector documentation](docs/collector.md) for package responsibilities, source limitations and R2 retention, and the [core delivery contract](https://github.com/NIPKaart/core/blob/main/docs/development/data-import-contract.md) for mappings, registration and review requirements.

## Contributing

Report bugs or propose a new source through [GitHub issues][issues-url]. For code changes, run the development checks above and open a pull request.

## License

[MIT](LICENSE)

<!-- MARKDOWN LINKS & IMAGES -->
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
