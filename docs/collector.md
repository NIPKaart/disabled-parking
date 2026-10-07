# Municipal collector

[Back to the README](../README.md)

This collector turns source package collections into complete municipal deliveries for NIPKaart. Packages handle source protocols; the collector maps and delivers records; core owns source approval, review and publication.

## Package collection contract

All connected municipal adapters call `parking_collection(parking_type=..., max_records=...)` and receive `ParkingCollection(records, total_count, pages_fetched, source_version, complete=True)`. The package owns source requests, pagination, parsing, original IDs, raw source attributes and completeness checks. The collector owns the approved selection, NIPKaart mapping, bounds checks, atomic file output and R2 delivery. See the [shared package contract](https://github.com/NIPKaart/core/blob/main/docs/development/data-import-contract.md#reusable-package-collection-contract) for the fields, errors and release order.

`max_records` is a safety ceiling, never a request to truncate. Source errors and observed count/version inconsistencies return no collection; the collector keeps its last valid delivery. A package may prove a complete empty selection, but the exporter still rejects empty deliveries. `source_version` is an opaque dataset-wide revision or `None`; Amsterdam has no verified dataset-wide revision, while Eindhoven and Namur compare Opendatasoft processing metadata before and after collection. This does not guarantee a transactional snapshot or current availability.

Capped/inspection methods stay available, but Eindhoven now uses only the v2.1 source endpoint and one `ParkingSpot` model. Its `spot_id` is the original `objectid`; consumers of the old portal `recordid` and `record_timestamp` must migrate with the major package release. Typed `ParkingData` and `Geometry` retain convenient source-field and coordinate access alongside complete `source_attributes`.

## Delivery format

Deliveries use `nipkaart-municipal-2`. Each file carries a `source` block from the dataset registry in [`app/datasets.py`](../app/datasets.py), so core can discover the dataset and an administrator can approve it once ([core ADR 0013](https://github.com/NIPKaart/core/blob/main/docs/adr/0013-discover-dataset-sources-from-deliveries-with-one-time-approval.md)): name, publisher, source URL, SPDX licence (`null` when the source publishes none), terms URL, attribution, ISO country and subdivision with the official municipality code (CBS for the Netherlands, INS for Belgium), bounds and the expected delivery interval. Every position of every record must lie within the bounds. Changing any of these values makes core ask for approval again, except `expected_interval_hours`.

## Source selections

Namur selects the public-road `PMR` records from the city's point dataset. The complete selection covers the published agglomeration, not the entire municipality. Original `identifiant` values are kept; long-term ID stability is not guaranteed by the publisher. General PMR access requires the appropriate parking card and does not imply current availability. Capacity and orientation remain unknown. Original parking-zone hours, dimensions and other claims are preserved in `source_attributes`; they are context, not automatically interpreted as PMR restrictions. `source_updated_at` uses `date_modif`, not portal processing time. The list is indicative and on-site signs remain authoritative.

Records keep the source's own claims in `source_attributes`. Source-specific rules stay in the adapters: Amsterdam delivers only general E6a bays and maps its bay orientation to the neutral `orientation` values `perpendicular`, `parallel` and `angle`; Eindhoven delivers points with `access_category` `unknown` and no orientation.

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

The Amsterdam, Eindhoven and Namur package releases are pinned exactly in [`pyproject.toml`](../pyproject.toml). [`uv.lock`](../uv.lock) records the resolved versions and distribution hashes. Update both files together and verify the collector tests and a local export for each changed source.

## Source review

Eindhoven remains recommended for source review: its public-domain reuse statement is verified, but general access, source-ID continuity and content currency remain unverified. See the [dated source assessment](eindhoven-source-review.md) for evidence and the questions requiring publisher confirmation. Core retains its normal one-time source approval; this recommendation does not introduce a dataset-specific runtime block. Dataset IDs have no legacy aliases or automatic migration.
