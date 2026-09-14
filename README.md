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

The manually reviewed handoff in [core#1215](https://github.com/NIPKaart/core/issues/1215) is complete. The producer uploads the same format to private Cloudflare R2; [core#1216](https://github.com/NIPKaart/core/issues/1216) implements automatic discovery and intake. No core database/API credentials or automatic publication are involved. See the [pilot source evidence](https://github.com/NIPKaart/core/blob/b068570/docs/development/data-import-pilot.md) and [file agreement](https://github.com/NIPKaart/core/blob/b068570/docs/development/data-import-contract.md). The government catalogue identifies the dataset as CC0; recheck the current API license before public use. The source announces future API-key requirements.

CI uses small package objects without live source requests. A separate live probe establishes source availability at that time, not an atomic snapshot or complete coverage of real-world parking.

## Scheduled producer

Run one persistent container on your Linux host. Amsterdam is the only enabled source. Copy `.env.example` to `.env`, fill in the private staging bucket endpoint and its S3 credentials, and restrict the file to your deployment user (`chmod 600 .env`). Use the endpoint shown for the bucket's jurisdiction; the example uses EU. Do not commit `.env`.

```bash
docker compose up -d --build
docker compose logs --tail 100 -f producer
docker compose stop
```

The internal scheduler starts immediately and waits 24 hours after success (`PRODUCER_INTERVAL_SECONDS`). Failures retry after at most five minutes. Every command has a five-minute deadline; fetching has its existing 180-second deadline and each SDK request has 10-second connection / 30-second read timeouts with at most three attempts. Runs are serial. Shared-volume locks prevent a second scheduler or one-shot producer from overlapping. Restarting the container starts another attempt immediately. Docker uses `unless-stopped`; logs rotate at three files of 10 MB. The container runs as UID 10001, with a read-only root filesystem, 512 MB memory limit and one CPU.

The named volume retains `pending.json` until R2 acknowledges delivery, then atomically replaces `last.json`. Upload retries reuse the exact pending bytes and delivery UUID before another fetch. The producer keeps at most these two 32 MiB files plus one temporary export; interrupted export temporary files are removed before the next fetch. Preserve this volume during restarts and updates. `docker compose down -v` destroys retry state and must not be used for routine updates.

Each delivery is one single PUT to `municipal/nl-amsterdam-parkeervakken-e6a/<delivery_id>.json`, with `Content-MD5`, SHA-256 metadata and `If-None-Match: *`. There is no manifest or multipart upload. If the response was lost but the object exists, the producer downloads it and compares exact bytes; a conflict fails and retains the pending file. These operations are documented in [R2's S3 compatibility reference](https://developers.cloudflare.com/r2/api/s3/api/). Core must validate downloaded bytes, format, scope and delivery identity before intake; upload success does not imply publication.

Use a dedicated private staging bucket, separate producer credentials and read-only core credentials. Producer operations need object write and recovery read access. Ordinary R2 object tokens are bucket-scoped and Object Read & Write also permits deletion; a key prefix and this program's create-only uploads are not an enforced credential restriction. Strict narrower rights and cleanup permissions must be verified in [core#1217](https://github.com/NIPKaart/core/issues/1217). Keep public access disabled. Rotate credentials by replacing `.env`, recreating the container with `docker compose up -d --force-recreate`, verifying a delivery and revoking the old token.

Retained R2 objects allow core to catch up after downtime without the producer contacting core. Before enabling unattended staging, configure retention longer than the accepted maximum core outage and agree the storage budget in #1217. No lifecycle policy or paid resource is provisioned by this repository. Before production, rehearse failed fetching, interrupted uploads, restart/retry and core downtime against actual isolated R2/core infrastructure. SDK-stub tests and Docker checks do not establish that operational acceptance.

For a one-shot upload, use the same environment and volume:

```bash
docker compose run --rm producer /app/producer.py
```

For local diagnosis without R2, the original exporter remains available:

```bash
uv run python export.py --city amsterdam --output /tmp/amsterdam.json
docker compose run --rm producer /app/export.py --city amsterdam --output /data/diagnostic.json
```

A `Producer failed` log leaves any pending file intact; inspect configuration and source availability, then retry. Identity conflicts require inspecting the local and remote files, not deleting the pending delivery or overwriting the remote object automatically. The scheduled collection itself detects source API changes using the same completeness and mapping checks as local export; external log alerting remains a hosting concern.

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
