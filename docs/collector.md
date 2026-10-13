# Municipal collector

[Back to the README](../README.md)

This collector turns source package collections into complete municipal deliveries for NIPKaart. Packages handle source protocols; the collector maps and delivers records; core owns source approval, review and publication.

## Package collection contract

Package-backed municipal adapters call `parking_collection(parking_type=..., max_records=...)` and receive `ParkingCollection(records, total_count, pages_fetched, source_version, complete=True)`. The package owns source requests, pagination, parsing, original IDs, raw source attributes and completeness checks. The collector owns the approved selection, NIPKaart mapping, bounds checks, atomic file output and R2 delivery. See the [shared package contract](https://github.com/NIPKaart/core/blob/main/docs/development/data-import-contract.md#reusable-package-collection-contract) for the fields, errors and release order.

`max_records` is a safety ceiling, never a request to truncate. Source errors and observed count/version inconsistencies return no collection; the collector keeps its last valid delivery. A package may prove a complete empty selection, but the exporter still rejects empty deliveries. `source_version` is an opaque dataset-wide revision or `None`; Amsterdam has no verified dataset-wide revision, while Eindhoven and Namur compare Opendatasoft processing metadata before and after collection. This does not guarantee a transactional snapshot or current availability.

Capped/inspection methods stay available, but Eindhoven now uses only the v2.1 source endpoint and one `ParkingSpot` model. Its `spot_id` is the original `objectid`; consumers of the old portal `recordid` and `record_timestamp` must migrate with the major package release. Typed `ParkingData` and `Geometry` retain convenient source-field and coordinate access alongside complete `source_attributes`.

## Delivery format

Deliveries use `nipkaart-municipal-2`. Each file carries a `source` block from the dataset registry in [`app/datasets.py`](../app/datasets.py), so core can discover the dataset and an administrator can approve it once ([core ADR 0013](https://github.com/NIPKaart/core/blob/main/docs/adr/0013-discover-dataset-sources-from-deliveries-with-one-time-approval.md)): name, publisher, source URL, SPDX licence (`null` when the source publishes none), terms URL, attribution, ISO country and subdivision with the official municipality code (CBS for the Netherlands, INS for Belgium), bounds and the expected delivery interval. Every position of every record must lie within the bounds. Changing any of these values makes core ask for approval again, except `expected_interval_hours`.

## Source selections

Namur selects the public-road `PMR` records from the city's point dataset. The complete selection covers the published agglomeration, not the entire municipality. Original `identifiant` values are kept; long-term ID stability is not guaranteed by the publisher. General PMR access requires the appropriate parking card and does not imply current availability. Capacity and orientation remain unknown. Original parking-zone hours, dimensions and other claims are preserved in `source_attributes`; they are context, not automatically interpreted as PMR restrictions. `source_updated_at` uses `date_modif`, not portal processing time. The list is indicative and on-site signs remain authoritative.

Records keep the source's own claims in `source_attributes`. Source-specific rules stay in the adapters: Amsterdam delivers only general E6a bays and maps its bay orientation to the neutral `orientation` values `perpendicular`, `parallel` and `angle`; Eindhoven delivers points with `access_category` `unknown` and no orientation.

Groningen uses the city's licensed WFS directly; there is no existing reusable Groningen package. It selects `TYPE='gehandicapten algemeen' AND ETYPE='E06'`, preserving all polygon rings and source claims. Personally reserved and unknown categories are excluded. Capacity and record-update dates remain unknown. The whole bounded selection must match the WFS counts and a repeated fetch of all claims; only the request-dependent feature IDs may change. IDs are preserved as received, never manufactured from coordinates. Core's municipal identity reconciliation must deploy before this collector is enabled: it retains parking UUIDs and requires explicit review for uncertain links. The source describes monthly updates and coverage of the schilwijken; daily delivery does not establish daily source observations. Source verification and two real delivery identities are recorded in the PR for [#811](https://github.com/NIPKaart/disabled-parking/issues/811).

Antwerpen selects all published disabled-parking polygons with `GISID IS NOT NULL AND GISID <> ''` from layer 585 (`be-antwerpen`, `identified-disabled-all`). On 2026-10-13 the complete layer had 1,848 records, one without GISID; the explicitly agreed identified subset has 1,847. The missing identity is a coverage limitation, never replaced with a row number or invented ID. The package checks source counts, unique GISID/OBJECTID values and two complete ordered reads; missing/duplicate IDs, short pages or observed source changes reject the collection. GISID continuity is not guaranteed by the publisher; OBJECTID only orders retrieval. Source errors preserve existing exports and dataset-specific pending deliveries.

Full WGS84 polygons and all rings remain intact. Capacity distinguishes unknown from zero, source orientation maps to neutral values, and access remains `unknown`: every inspected row says `toegang=Beperkt`, with 25 time-window claims despite the layer description saying no time-window regime. Personally reserved access cannot be distinguished from this field. Core review must assess signage and preserved restrictions before publication. Street and record-update time remain unknown; `EBDD` is not a verified modification timestamp. The publisher describes daily maintenance of a 2018 paid-parking-area inventory, not current observations or full municipal coverage.

Evidence checked 2026-10-13: [municipal GIS layer](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek6/MapServer/585), [publisher item and daily cadence](https://www.arcgis.com/sharing/rest/content/items/3b69e4d15fc14fbb86a00d6c636da475?f=json), [Gratis Open Data Licentie](https://www.antwerpen.be/info/gratis-open-data-licentie), and [municipal parking information](https://www.antwerpen.be/parkeren-voor-personen-met-een-handicap). The city's reuse terms require `bron stad Antwerpen`; no verified SPDX identifier is assigned to this licence, so `licence` stays `null`. Delivery/intake evidence belongs to the PR for [#813](https://github.com/NIPKaart/disabled-parking/issues/813). The collector uses the published `antwerpen==2.0.0` release from [package PR #1259](https://github.com/klaasnicolaas/python-antwerpen/pull/1259), pinned exactly with distribution hashes in the lockfile. Production activation stays at core #1303.

## Retention

Deliveries go to the private EU bucket `nipkaart-imports` under `municipal/<dataset>/`. Core also archives manual uploads there. Set one lifecycle rule on the bucket, once:

| Rule name | Prefix | Delete after | Why |
| --- | --- | --- | --- |
| `expire-municipal` | `municipal/` | 30 days | Well beyond the 7-day core outage window; covers every dataset |

Never add a rule without a prefix: the bucket also holds offstreet deliveries with their own rules (see [offstreet-parking](https://github.com/NIPKaart/offstreet-parking#retention)).

**Dashboard:** R2 → `nipkaart-imports` → Settings → Object lifecycle rules → Add rule. Enter the name and prefix, choose to delete objects after 30 days, and save. If an older rule only covers `municipal/nl-amsterdam/`, replace it with this one.

**Or with Wrangler** (after `npx wrangler login`; the bucket is in the EU jurisdiction):

```bash
npx wrangler r2 bucket lifecycle add nipkaart-imports expire-municipal municipal/ --expire-days 30 --jurisdiction eu
npx wrangler r2 bucket lifecycle list nipkaart-imports --jurisdiction eu
```

## Dependencies

The Amsterdam, Antwerpen, Arnhem, Eindhoven, Namur and Stockholm package releases are pinned exactly in [`pyproject.toml`](../pyproject.toml). [`uv.lock`](../uv.lock) records the resolved versions and distribution hashes. Update both files together and verify the collector tests and a local export for each changed source.

## Source review

Use one compact assessment per source: dataset and check date, then a table with **topic, conclusion, mapping/handling and evidence**, followed by the decision. Cover reuse, access, identity, currency and completeness. Keep evidence in one place and link to it from collector and core documentation. Unknown source values are recorded as unknown; additional publisher confirmation is needed only when the intended mapping or publication claim requires it.

[Eindhoven's assessment](eindhoven-source-review.md) records accepted public-domain reuse, original IDs and unknown access/currency. Intake and publication use core's existing source approval and review. Dataset IDs have no legacy aliases or automatic migration.

[Stockholm's assessment](stockholm-source-review.md) records the complete 2,294-record source check, real private-R2 delivery and isolated core acceptance. Stockholm retains original regulation lines and unknown access/capacity/currency; one collapsed component requires explicit geometry review in core. Configure `STOCKHOLM_API_KEY` for collection. Stockholm uses the published package release v2.0.0; the core companion must land before merging/deploying this collector integration.
