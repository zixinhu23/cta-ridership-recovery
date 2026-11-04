# Data Dictionary

## Source and scope

The data come from the Chicago Transit Authority Annual Ridership Reports for
calendar years 2019 and 2025. The reports are included in this repository and
are also linked from the README.

The analysis covers rail station entries. Station and line form a composite
key because names such as Addison, Kedzie, and Western occur on multiple lines.

## Annual extraction files

### `cta_station_entries_2019.csv`

| Column | Type | Description |
|---|---|---|
| `station` | string | Canonical CTA station name |
| `line` | string | CTA line under which the report lists the station |
| `entries_2018` | integer | Annual station entries in 2018 |
| `entries_2019` | integer | Annual station entries in 2019 |

### `cta_station_entries_2025.csv`

| Column | Type | Description |
|---|---|---|
| `station` | string | Canonical CTA station name |
| `line` | string | CTA line under which the report lists the station |
| `entries_2024` | integer | Annual station entries in 2024 |
| `entries_2025` | integer | Annual station entries in 2025 |

Each annual file contains 142 station totals. The station names are normalized
to remove entrance suffixes and report labels such as `Red,` or `Brown,
Orange,`.

## Analysis file

### `cta_station_recovery.csv`

| Column | Type | Description |
|---|---|---|
| `station` | string | Canonical CTA station name |
| `line` | string | CTA line used in the matched analysis |
| `entries_2019` | integer | Annual station entries in 2019 |
| `entries_2025` | integer | Annual station entries in 2025 |
| `recovery_pct` | float | `100 * entries_2025 / entries_2019` |
| `comparable` | boolean | Whether the station is included in the recovery comparison |
| `analysis_note` | string | Reason a retained station is not comparable |

The matched file contains 140 stations.

## Matching and exclusions

- Kildare appears only in the 2019 report and is absent from the 2025 report.
- Damen station on the Green Line appears only in the 2025 report because it
  reopened in 2024, so it has no 2019 comparison.
- The two reports share 141 station-line pairs. Kostner has 97,285 entries in
  2019 and is removed by the 100,000-entry threshold, leaving 140 rows.
- Berwyn and Lawrence reopened on July 20, 2025 after long closures. Their 2025
  annual totals reflect only part of the year, so they remain in the CSV with
  `comparable=False` and are excluded from the recovery analysis.
- The analysis requires at least 100,000 entries in 2019 to limit unstable
  percentage changes at low-volume stations.

After these rules, 138 stations are used in the final analysis.

## Interpretation notes

- Station entries count boardings, not unique riders.
- Ridership is a usage measure, not a complete measure of accessibility.
- CTA changed its 2025 ridership processing methodology, so the two years are
  not perfectly comparable.
- The reported median recovery for the 138 comparable stations is 66.2%.
