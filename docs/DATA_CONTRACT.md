# Data contract (Phase B)

What the site reads from `public/data/`, what each file holds, how big it may be, and what limit statement it carries. Fitted to what B1 found in the v1 zip (see `docs/DATA_NOTES.md`). Page names are provisional: `docs/DECISIONS_SITE.md` and `docs/SUBMISSION_RULES.md` were not found.

Items marked **OPEN** need a decision at the Phase B gate. Items marked "not in v1 outputs" cannot be filled.

## Rules for every file

- Built by one command (`make_data`, B5) from the v1 zip and the site CSV. Never edited by hand.
- Deterministic: sorted keys, fixed number formatting, no timestamps, LF line endings, UTF-8, trailing newline.
- Read-only lookup of stored v1 values. No new score, no estimate, no back-fill.
- A value that v1 did not store is the string `"not in v1 outputs"`. Never `null`, `0` or a guess.
- Numbers keep full v1 precision in data files. Display rounding is fixed: scores and percentiles 1 decimal, counts as integers, areas as integers. Site text takes the rounded string from `claims.csv`.
- Every JSON file starts with a header object `meta`:
  - `schema_version` (integer, 1)
  - `file` (published path)
  - `label` (plain statement of what the file is, for example "descriptive lookup of stored v1 scores, not a test")
  - `limits` (array of strings: what this data cannot show, where the analogy breaks down)
  - `sources` (array of `{source_file, sha256}`; v1 files are given as the path inside the zip)
- Banned words (CLAUDE.md, decision E32) never appear in any text field.
- Field names use plain terms. The v1 field `robust` is published as `top5_in_90pct_runs`. Site text says "flagged in the top 5% in at least 90% of runs".
- Nothing here claims the ranking is checked against independent data. It is not.

## Identifiers

- `target`: `connecting_ridge_c1`, `shackleton_rim` (Moon, standard confidence); `jezero` (Mars, low confidence).
- `profile`: `base`, `landing_mobility`, `power_night` (Moon and Mars); `ice_resources` (Mars only). Not run: Moon `ice_resources`, Mars `geology_life`, Mars Arcadia (unscored).
- `view`: `<target>__<profile>`. 10 full-globe views exist (6 Moon, 4 Mars). 6 more exist in the latitude 20 to 40 band-check run; those appear in `metrics.json` only.
- `tile_id`: integer, `iy * 5790 + ix`, EPSG:6933 6 km grid. Each tile has an exact area of 36 km2.
- Display names: `connecting_ridge_c1` is "Connecting Ridge C1" (never "C2"); `shackleton_rim` is "Shackleton rim"; `jezero` is "Jezero".
- Coordinates: decimal degrees, 4 decimals, WGS84.

## Files

### `sites.json`

| | |
|---|---|
| Serves | (a) identify and (b) characterise analog locations; (c) limits |
| Read by | sites list and site detail pages |
| Source | `data/reference/sites.csv` (B2), exported from Supabase when B13 exists, otherwise built from the CSV |
| Expected size | up to 50 sites, about 30 KB. Limit 100 KB |
| Today | **0 sites.** All 120 CSV rows fail the two-source rule (no source URL column). See `data/reference/sites_check.md`. |

Fields per site: `id` (slug of name and body), `name`, `body`, `lat`, `lon`, `kind`, `analog_of`, `source_url_1`, `source_url_2`, `v1_used` (`true`, `false` or `unknown`), `v1_match` (`{site_id, km}` or `"not in v1 outputs"`), `limits`.

- `kind` and `analog_of`: no matching column in the CSV. **OPEN**: needs a value from Anay or Yash, otherwise `"not in v1 outputs"` is wrong (they are not v1 outputs at all). Proposed: leave empty and hide on the page.
- `limits`: per-site statement of where the analogy breaks down. The CSV has a free-text column for this, written by hand with unreferenced numbers (for example sun angle, day length). **OPEN**: use it only after each number gets a claims row, or replace it with the v1 ledger rows that apply to the body.
- The CSV numeric columns (similarity, Monte Carlo band, per-parameter scores) are not v1 outputs and are not published.

### `site_lookup.json`

| | |
|---|---|
| Serves | (a) and (b); (c) via status and limits |
| Read by | site detail page, sites list |
| Source | `base_scores.parquet` and `mc_summary.parquet` per view; `validation.json` for the v1 reference sites |
| Expected size | about 10 views by 50 sites, 500 entries, about 120 KB. Limit 300 KB |

- Header `meta.label`: "Descriptive lookup of stored v1 scores at known sites. This is not a test."
- Header `meta.limits` includes: tiles are 6 km; scores exist only for tiles that passed the land-cover and data gates; the Moon score uses terrain only; slope is not corrected for the map projection; v1 failed its negative controls.
- Per site, per view: `status` (`scored`, `gated_out`, `no_tile`), `tile_id`, `km_to_tile`, `score`, `percentile`, `top5_in_90pct_runs`.
- Site to tile rule: same as v1 (`validation.json` `site_score_rule`): the best-scoring tile that passed the gates, within 20 km of the site point. If every tile in range failed a gate: `gated_out`, no score. If no land tile in range: `no_tile`.
- `percentile`: **OPEN.** The brief says "among land tiles". v1 stores rank percentile among gated tiles that scored (about 31% of land tiles for the Moon), and gated-out tiles have no score to rank. The proposed definition is v1's: percentile among tiles that passed the gates. Computing it from stored scores is a rank, not a new score; confirm that reading.
- Summaries, two groups (v1 used the site: yes, no) with `n` and `median_percentile` only. `unknown` rows are counted in neither group and listed separately as `n_unknown`. **Today n is 0 in every group** because `sites.json` is empty.

### `tiles_top.json`

| | |
|---|---|
| Serves | (a) identify candidates not in our reference list |
| Read by | candidates table, map markers |
| Source | `mc_summary.parquet` and `base_scores.parquet` per view (the zip also holds top-500 exports) |
| Size limit | **400 KB raw**. Set at 100 tiles per view for the 10 full-globe views: about 1,000 tiles at about 130 bytes each, about 130 KB, with headroom |

- Per view: `target`, `profile`, `confidence`, `n_gated_tiles`, `n_top5_in_90pct_runs`, then `tiles`.
- Tile fields: `tile_id`, `lat`, `lon`, `score`, `mc_median`, `mc_p05`, `mc_p95`, `freq_top5`, `top5_in_90pct_runs`, `illum_match`, `nearest_v1_site`, `km_to_nearest_v1_site`, `in_india`.
- Family scores: v1 stores one family value per tile (`illum_match`, the lighting family). Slope, roughness and relief family scores are `"not in v1 outputs"` and the key is omitted rather than filled.
- `in_india`: from `site_data/*india*.csv` flags (Natural Earth outline, not an official map). Label only.
- Tile order: by `top5_in_90pct_runs` (true first), then `mc_median` descending, then `tile_id` ascending.
- Limits: scores compare Earth tiles to one lunar or Martian target; the Moon score is effectively terrain only; Mars is low confidence (four families); tile scores carry no information on gravity, air, dust or radiation.

### `overlays/<target>.png`, `overlays/<target>.json`, `overlays/legend.png`, `overlays/legend.json`

| | |
|---|---|
| Serves | (a) where scores are high; (b) what the score is |
| Read by | map page |
| Source | `base_scores.parquet`, `base` profile, one per target |
| Expected size | 3 PNGs, each at most 1.5 MB; total under 5 MB. Limit per PNG 2 MB |

- One equirectangular PNG per target (3 files). Transparent where v1 has no score (no data, water, gated out).
- Sidecar JSON per overlay: `bounds` (`west`, `south`, `east`, `north`), `width`, `height`, `crs` (`EPSG:4326`), `resampling`, `value_range`, `colour_scale`, `limits`.
- Legend: shared colour stops and labels. Colour scale and resampling method are written to `docs/DATA_NOTES.md` (B6).
- Limits: resampling smooths 6 km tiles; masked tiles are not low scores, they are unscored.
- Overlay colours show the base profile only. Other profiles are available as tiles in `tiles_top.json`.

### `regions.json`

| | |
|---|---|
| Serves | (a) candidates not in our reference list |
| Read by | regions page, map |
| Source | `mc_summary.parquet` flags per view |
| Expected size | about 100 regions, about 80 KB. Limit 150 KB |

- Fields per region: `id` ("Region NN"), `target`, `profile`, `n_tiles`, `area_km2` (n_tiles by 36), `centroid_lat`, `centroid_lon`, `bbox`, `median_score`, `median_mc_median`, `km_to_nearest_reference_site`, `nearest_place`, `status` ("Unreviewed"), `caveat`.
- Cluster rule: tiles flagged top 5% in at least 90% of runs, joined by 8-neighbour adjacency on the grid (wrapping at the date line). If flags were missing the fallback is the top 1% by score, labelled "exploratory". Flags exist, so the fallback is not used.
- Drop rule: clusters within 100 km of any reference site (the 100 km value is v1's own `discovery.min_distance_km`).
- **OPEN, cluster size.** Raw clusters: 4,711 (Shackleton rim, base), 6,421 (Connecting Ridge C1, base), 9,937 (Jezero, base). Most are 1 to 4 tiles. A minimum size is needed. Counts of clusters at least 25 tiles: 168, 1, 300; at least 100 tiles: 38, 0, 48. The "Region NN" format fits at most 99. Proposed: minimum 100 tiles (3,600 km2).
- **OPEN, which views.** Proposed: `base` profile of each target only; Mars labelled low confidence.
- **OPEN, reference list.** The drop rule uses "the 50 sites". Today that list is empty. v1's own list has 18 entries (`known_sites.yaml`).
- **BLOCKER, `nearest_place`.** No gazetteer in the zip. Until one is chosen the field is `"not in v1 outputs"` and region names are the id alone.
- Caveat text, same for every region: "Flagged by v1 on Earth terrain only. Not reviewed. Not checked against independent data. v1 failed its negative controls."

### `metrics.json`

| | |
|---|---|
| Serves | (c) where the method fails; (d) provenance |
| Read by | results page, failures page, home page |
| Source | `validation.json` (3 runs), `summary.json` (16 views), `run_summary.json`, `alt_weight_checks.json`, `earth_coverage.json` |
| Expected size | about 25 KB. Limit 60 KB |

- Each metric: `id`, `value`, `unit`, `source_file`, `sha256`, `what_this_means_for_the_analogy`.
- Contents: pre-registered criteria and their status per run; control rank percentiles (Namib, Rub' al Khali, Amazon and Congo as gated out); primary site percentiles; Mars primary median; Moon terrain-only test results (overlap, Spearman, `illum_match` ceiling); `n_robust` per view (published as `n_top5_in_90pct_runs`); `n_gated_tiles`; run counts; land tile coverage (share of land tiles with terrain data).
- Every `what_this_means_for_the_analogy` states a limit. No entry reads as a success.

### `ledger.json`

| | |
|---|---|
| Serves | (c) where the analogy breaks down |
| Read by | failures page, method page |
| Source | `config/ledger.yaml`, `results/*/validation.json`, `results/*/export/fidelity.json`, `docs/UNVERIFIED.md` |
| Expected size | about 30 KB. Limit 60 KB |

- Entry fields: `id`, `type` (`failed_control`, `unscored_property`, `known_limit`, `physical_difference`), `statement`, `body`, `status`, `provisional`, `source_file`, `sha256`, `what_this_means_for_the_analogy`.
- `physical_difference` rows come from the v1 limits ledger (gravity, air pressure, cold traps, polar lighting, radiation, regolith, rock chemistry, and others). v1 marks most as provisional and unverified; that flag is kept.
- Also carries: pre-registration hash per run, the unscored families (temperature, composition, thermal inertia for the Moon; roughness, composition, water, dust for Mars), slope not corrected for the projection, the 60 N terrain seam, the 11 unconfirmed site coordinates.
- The E32 uncertainty sentence is printed from `docs/E32.txt` into the header `meta.uncertainty_sentence`, verbatim. It is never retyped.

### `claims.csv`

| | |
|---|---|
| Serves | all: every number on the site traces to a source |
| Read by | claims check (B11); not read by pages |
| Expected size | about 400 rows, about 60 KB. Limit 150 KB |

- Columns, in this order: `claim`, `number`, `source_file`, `sha256`.
- `claim`: a stable dotted id plus a short statement, for example `moon.control.namib_sand_sea.rank_pct`.
- `number`: the display string exactly as pages print it ("90.2", "2000", "36").
- `source_file`: path of the file the number comes from: a path inside the v1 zip for v1 facts, or a path under `public/data/` for derived counts.
- `sha256`: sha256 of that file (v1 value from `FILES.sha256`; derived value computed by the build).
- Sorted by `claim`. Quote only when needed.
- **OPEN, extra column.** The check also needs the place inside `public/data/` where the site reads the number. Proposed fifth column `data_pointer`. Not added without a go.

### `MANIFEST.csv`

- Lives at **`data/MANIFEST.csv`**, not in `public/data/`. A manifest inside the folder it describes cannot hash itself, and it should not be served.
- Covers every file under `public/data/` (recursive) and `data/reference/sites.csv`. Does not list itself.
- Columns: `path`, `bytes`, `sha256`. Sorted by `path`. Paths are repo-relative with `/` separators.
- Written last by `make_data`. Two runs from a clean state must give byte-identical output.

## Which page reads which file

| File | Pages (provisional) |
|---|---|
| `sites.json` | sites list, site detail |
| `site_lookup.json` | site detail, sites list |
| `tiles_top.json` | candidates table, map |
| `overlays/*` | map |
| `regions.json` | regions, map |
| `metrics.json` | results, failures, home |
| `ledger.json` | failures, method |
| `claims.csv` | none (CI check only) |
| `MANIFEST.csv` | none (CI check only) |

## Size budget

| File | Limit |
|---|---|
| `sites.json` | 100 KB |
| `site_lookup.json` | 300 KB |
| `tiles_top.json` | 400 KB |
| `overlays/<target>.png` | 2 MB each |
| `regions.json` | 150 KB |
| `metrics.json` | 60 KB |
| `ledger.json` | 60 KB |
| `claims.csv` | 150 KB |
| Whole `public/data/` | 8 MB |

No file approaches 50 MB. The build fails if a limit is exceeded.

## Not in v1 outputs

- Per-tile family scores for slope, roughness and relief.
- A gazetteer (place names for regions).
- Source URLs for the 120 CSV rows.
- Site `kind` and `analog_of` values.
- A percentile among all land tiles (gated-out tiles have no score).
- Any Moon temperature, composition or thermal inertia score; any Mars water, silica, dust or temperature score.
- Illumination for Earth sites matching a lunar polar target (illumination family is about zero everywhere).
