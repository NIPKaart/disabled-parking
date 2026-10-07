# Eindhoven source review

[Back to the collector documentation](collector.md)

Checked on **2026-10-07** for [issue #821](https://github.com/NIPKaart/disabled-parking/issues/821). This review separates data reuse rights from permission to use an individual parking bay.

## Reuse rights

The municipality labels the dataset's licence `Publiek domein`. The [official v2.1 metadata](https://data.eindhoven.nl/api/explore/v2.1/catalog/datasets/parkeerplaatsen) supplies no licence URL or attribution requirement. The [government catalogue entry](https://data.overheid.nl/dataset/1bcae1d3-33fe-46fb-a82c-6c2d6db42920) also records public access and public-domain reuse, including the downloadable distributions.

The portal's [terms and conditions](https://data.eindhoven.nl/terms/terms-and-conditions/) present Eindhoven's Smart Society Charter. Its public-space data principles support commercial and non-commercial use, equal access and free provision, subject to privacy and security. These are general portal principles, not an identified CC0 dedication or Public Domain Mark for this dataset.

Decision: reuse is supported by the publisher's public-domain statement. Preserve that statement and its evidence in the source review. Keep `licence` null in the delivery's SPDX field because no specific SPDX licence has been verified; do not silently translate the label to `CC0-1.0`. Retain the official dataset URL as the source terms evidence and Gemeente Eindhoven as attribution/provenance. A publisher-supplied licence identifier or licence URL would permit a more precise machine-readable value.

## General and personally reserved parking

Eindhoven's [parking-card guidance](https://www.eindhoven.nl/stad-en-wonen/stad/parkeren/gehandicaptenparkeren/gehandicaptenparkeerkaart) distinguishes general disabled bays from permit-holder spaces. It allows parking-card holders to use general disabled bays, including those within permit zones; a bay's specific time limit still applies. This guidance does not identify the access class of each dataset record.

The municipality separately offers [personally reserved disabled bays](https://www.eindhoven.nl/stad-en-wonen/stad/parkeren/gehandicaptenparkeren/gehandicaptenparkeerplaats). These are assigned to a vehicle registration and other vehicles may not use them. Their existence means a disabled-parking designation alone is insufficient to prove general access.

The [dataset description and schema](https://data.eindhoven.nl/explore/dataset/parkeerplaatsen/?flg=nl-nl) describe parking locations accessible from public space and expose `type_en_merk` as a parking-type indication. The published fields contain no dedicated general/reserved flag, vehicle registration, beneficiary or sign restriction. The value `Parkeerplaats Gehandicapten` therefore does not prove that every selected bay is general. Conversely, the reviewed evidence does not establish that personally reserved bays are included; that remains an unanswered source question.

Decision: retain `access_category=unknown` and allow source review, but do not approve the selection as general disabled parking for public discovery. Approval requires an authoritative definition that excludes personally reserved bays, a source field/filter that distinguishes them, or verified record-level access classification. A count, public-domain licence or publicly accessible road location cannot satisfy that gate. On-site signs determine the actual conditions of use.

## Source identity

The [referenced municipal GIS layer](https://gisservice.eindhoven.nl/arcgis/rest/services/Parkeren_Pres_Verg_TH/MapServer/2?f=pjson) defines `OBJECTID` as `esriFieldTypeOID`, with a unique index. Its published fields contain no GlobalID, durable business identifier or creation/edit timestamps. The open-data portal preserves this value as `objectid`.

On 2026-10-07 the [filtered portal query](https://data.eindhoven.nl/api/explore/v2.1/catalog/datasets/parkeerplaatsen/records?where=type_en_merk%3D%27Parkeerplaats%20Gehandicapten%27&order_by=objectid&limit=100&offset=0) reported 180 records, retrieved over two pages. The [GIS query](https://gisservice.eindhoven.nl/arcgis/rest/services/Parkeren_Pres_Verg_TH/MapServer/2/query?where=TYPE_EN_MERK%3D%27Parkeerplaats%20Gehandicapten%27&outFields=*&outSR=4326&orderByFields=OBJECTID&f=json) also returned 180 records without a transfer-limit flag. All 180 positive unique IDs matched between the two sources, as did street, type and numeric capacity. This proves current identity passthrough, not continuity across a future source rebuild.

[Esri documents](https://support.esri.com/en-us/knowledge-base/is-it-recommended-to-use-objectids-when-joining-a-table-000012462) that ObjectIDs identify rows in the original feature class but can be reassigned when importing, exporting or overwriting data. Eindhoven's published schema and metadata do not promise retention across such operations. Continue preserving original IDs for review; do not invent a coordinate-derived replacement or claim permanent identity. Public approval needs a publisher statement about the actual maintenance process or a supported durable identifier.

## Data currency

The [official metadata](https://data.eindhoven.nl/api/explore/v2.1/catalog/datasets/parkeerplaatsen) still states `metas.dcat.temporal = "t/m juli 2018"`. Its `modified` and `data_processed` timestamps are `2026-09-15T13:42:49+00:00`; the metadata says `modified` can change on both metadata and data changes. `update_frequency` and `accrualperiodicity` are null. Neither the portal nor the referenced GIS layer exposes a per-record survey/edit date.

Matching the current GIS selection establishes that the portal exposes the same 180 IDs and listed attributes today. It does not establish when a bay was last inspected, whether removed bays have been retired, or whether the temporal description is stale. Do not use portal processing time as `source_updated_at`; retain `None`. Content currency remains unverified, not conclusively frozen in 2018.

## Publication decision

**Retain for source review.** The public-domain reuse statement is established, but general-access classification, identity continuity through source updates and content currency are not sufficiently established for public discovery. Preserve `access_category=unknown`, `source_updated_at=None` and original source attributes. Do not silently map the selection to general parking or manufacture a CC0 identifier.

This is a source assessment, not a dataset-specific runtime block. Core continues to use its existing one-time source approval, intake and publication workflow. No source has been approved, uploaded or publicly activated by this investigation. Production activation remains [core #1303](https://github.com/NIPKaart/core/issues/1303).

## Questions still requiring publisher evidence

- Does `type_en_merk='Parkeerplaats Gehandicapten'` contain exclusively general bays, or does it also contain bays assigned to individual vehicle registrations?
- If both occur, which official attribute or related dataset distinguishes them, and what is the supported record join?
- Are `OBJECTID` values retained through normal updates, deletions, source replacement and republication? Is a durable business ID available?
- When were the records last substantively surveyed or updated, and how are removed or changed bays maintained? Is “t/m juli 2018” still the intended temporal scope?
- Which concrete public-domain instrument, if any, applies to the dataset's reuse statement? This would refine the SPDX field; it does not settle access or currency.

The metadata lists `data@eindhoven.nl` as publisher contact. No message has been sent to the municipality. Keep these questions visible in issue #821 until authoritative evidence supports a revised decision.
