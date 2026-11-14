# Data contract (Phase B)

What the site reads from `public/data/`, what each file holds, how big it is, and what limit statement it carries. This version matches the files `make_data` builds today. Page names are provisional: `docs/DECISIONS_SITE.md` and `docs/SUBMISSION_RULES.md` were not found.

Build: `python3 scripts/make_data.py` (needs `scripts/requirements.txt`). Check: `python3 scripts/check_claims.py` (standard library only; runs in CI).

## Rules for every file

- Built by one command from the v1 zip and the site CSV. Never edited by hand.
- Deterministic: sorted keys, fixed number formatting, no timestamps, LF line endings, UTF-8. Two clean runs give identical bytes.
- Lookup of stored v1 values. No new score, no estimate, no back-fill. The only computed values are ranks, distances, counts, medians and cluster geometry over stored values.
- A value v1 did not store is the string `"not in v1 outputs"`.
- Every JSON file starts with `meta`: `schema_version`, `file`, `label`, `limits` (array of strings), `sources` (array of `{source_file, sha256}`), and `facts` where text uses a number.
- Source paths for v1 files start with `gsop_v1/` (path inside the zip). Hashes come from the zip's own `FILES.sha256`.
- Text written by this build contains no typed numbers. A number in text is read from a stored field and listed in `meta.facts` with its source.
- Banned words (decision E32) never appear. The v1 field `robust` is published as `top5_in_90pct_runs`.
- Nothing claims the ranking is checked against independent data. It is not.

## Identifiers

- `target`: `connecting_ridge_c1`, `shackleton_rim` (Moon, standard confidence); `jezero` (Mars, low confidence).
- `profile`: `base`, `landing_mobility`, `power_night` (Moon and Mars); `ice_resources` (Mars only). Not run: Moon `ice_resources`, Mars `geology_life`, Mars Arcadia.
- `view`: `<target>__<profile>`. 10 full-globe views. 6 more exist in the latitude 20 to 40 band check; they appear in `metrics.json` only.
- `tile_id`: `iy * 5790 + ix` on the EPSG:6933 6 km grid. Each tile is exactly 36 km2.
- A site is only compared with views of its own body (Moon list with Moon views, Mars list with Mars views).

## Display formats

`claims.csv` holds the display string. Pages print that string, never a reformatted value.

| Quantity | Decimals |
|---|---:|
| scores, Monte Carlo scores, percentiles, medians, km to tile | 1 |
| km to nearest reference site, counts, areas | 0 |
| latitude, longitude, share of runs (`freq_top5`) | 2 |
| `illum_match` | 3 |
| ratios in metrics (overlap, correlation, weights, shares) | 4, truncated, never rounded up to 1 |

Data files keep 4 decimals for scores and coordinates (6 for metric values), which is as precise as v1's stored 32-bit values.

## Files

### `sites.json`
- Serves (a), (b), (c). Read by site list and detail pages. 100 sites, 53 KB, limit 100 KB.
- Source: `data/reference/raw/GSOP_analog_sites_moon_mars.csv`, only the rows labelled as known sites (50 Moon, 50 Mars). The 20 candidate rows are not reference sites and are left out here; see `data/reference/sites_check.md`. Column mapping decisions are in `docs/sites_mapping.md`.
- Fields: `id`, `name`, `body`, `lat`, `lon`, `kind`, `analog_of`, `source_url_1`, `source_url_2`, `coordinates_approximate`, `v1_used`, `v1_match` (`{site_id, km}`), `limits`, `limits_source`.
- The two-source rule was relaxed by instruction. The CSV has no URLs, so both source fields read `"not provided in site CSV"`.
- `kind` and `analog_of` are `null`, as in `docs/sites_mapping.md`: `Process_type` is ambiguous and a person decides; the CSV has no analog target column.
- `limits` is the CSV `Where_analogy_breaks` text. It is LLM-written and unreviewed. Numbers inside it and inside site names get claims rows that cite the CSV.
- `v1_used`: `true` within v1's match radius of a v1 site run for that body; `unknown` near a v1 site but not matching; `false` beyond v1's exclusion distance of every v1 site.
- The CSV's similarity numbers, Monte Carlo bands and gate labels are not v1 outputs and are not published.

### `site_lookup.json`
- Serves (a), (b), (c). Read by site detail and list pages. 500 entries, 162 KB, limit 300 KB.
- `meta.label`: "Descriptive lookup of stored v1 scores at reference sites. This is not a test."
- Rule for site to tile: v1's own. The best-scoring tile that passed the gates within the match radius (read from v1's `run.yaml`).
- Percentile: v1's own, `100 * (tiles with a lower score) / (tiles that passed the gates in that view)`. Checked against v1: Haughton and Mars Desert Research Station reproduce v1's stored values to every digit.
- Entry per site and view: `status` (`scored`, `gated_out`, `missing_data`, `no_land_tile`), and for `scored`: `tile_id`, `km_to_tile`, `score`, `percentile`, `top5_in_90pct_runs`. Other statuses carry `reason` and no score.
- `summary_by_view`: per view, `v1_used_true` and `v1_used_false` each with `n` (sites with a percentile), `n_group` (sites in the group) and `median_percentile`; `v1_used_unknown` with counts only.
- Today: 338 scored, 76 gated out, 56 missing data, 30 with no land tile.

### `tiles_top.json`
- Serves (a). Read by candidates table and map. 301 KB, limit 400 KB.
- Top 100 tiles for each of the 10 views. Order: flagged first, then Monte Carlo median, then tile id.
- View fields: `target`, `profile`, `body`, `confidence`, `illum_match_family`, `n_gated_tiles`, `n_top5_in_90pct_runs`, `source_file`, `sha256`, `tiles`.
- Tile fields: `tile_id`, `lat`, `lon`, `score`, `mc_median`, `mc_p05`, `mc_p95`, `freq_top5`, `top5_in_90pct_runs`, `illum_match`, `in_india`, `nearest_reference_site`, `km_to_nearest_reference_site`.
- Family scores: v1 stores only the lighting family per tile (`illum_match`). Slope, roughness and relief family scores per tile are not in v1 outputs and are omitted.
- `in_india` comes from v1's own flag (Natural Earth outline, not an official map).

### `overlays/<target>.png`, `<target>.json`, `legend.png`, `legend.json`
- Serves (a), (b). Read by the map page. Three PNGs of 0.3 to 0.45 MB each, limit 2 MB.
- Base profile, one per target. Equirectangular, west -180 to east 180, south -55.4 to north 82.9, 3600 by 1383, 0.1 degree pixels. Transparent means no v1 score.
- Colour scale, resampling and known artifacts are in `docs/DATA_NOTES.md`.

### `regions.json`
- Serves (a). Read by regions page and map. 82 regions, limit 150 KB.
- Cluster rule: tiles flagged top 5% in at least 90% of runs (v1's flag), base profile of each target, joined by 8-neighbour adjacency, wrapping at the date line.
- Parameters set in this build: minimum 100 tiles (a build choice, listed as a fact whose source is `scripts/gsop_data/regions.py`); drop clusters within 100 km of any reference site (v1's own `min_distance_km`).
- Result by view: Shackleton rim 36, Jezero 46, Connecting Ridge C1 0. Raw clusters per view: 4,711, 9,937, 6,421. See `meta.by_view`.
- Fields: `id` ("Region NN"), `target`, `profile`, `body`, `confidence`, `n_tiles`, `area_km2`, `centroid_lat`, `centroid_lon`, `bbox`, `median_score`, `median_mc_median`, `km_to_nearest_reference_site`, `nearest_reference_site`, `n_tiles_in_india`, `nearest_place`, `status` ("Unreviewed"), `caveat`.
- `nearest_place` is `"not in v1 outputs"`. No gazetteer has been chosen. Blocker.
- `n_tiles_in_india` uses a point-in-polygon test against v1's outline; the test agrees with v1's own flags on its top-500 file.

### `metrics.json`
- Serves (c), (d). Read by results, failures and home pages. 146 entries, 74 KB, limit 100 KB.
- Entry: `id`, `group`, `label`, `unit`, `value`, `display`, `source_file`, `sha256`, `what_this_means_for_the_analogy`.
- Groups: pre-registration hashes and thresholds, criteria status per run, primary site and control results, per-view counts, Moon terrain-only tests, latitude band counts, coverage, physical match score.
- Every `what_this_means_for_the_analogy` states a limit.

### `ledger.json`
- Serves (c). Read by failures and method pages. 35 entries, 23 KB, limit 60 KB.
- Entry: `id`, `type` (`failed_control`, `known_limit`, `unscored_property`, `physical_difference`), `body`, `status`, `provisional`, `statement`, `source_file`, `sha256`, `what_this_means_for_the_analogy`.
- Header carries the E32 sentence verbatim in `meta.uncertainty_sentence` (compared with `docs/E32.txt` at build and in CI) and both pre-registration hashes in `meta.preregistration_hashes`.

### `claims.csv`
- Columns: `claim`, `number`, `source_file`, `sha256`. Sorted by `claim`. 11,185 rows, 2.1 MB, limit 3 MB.
- Rows come from: every `meta.facts` entry; numeric metrics; per-tile values in `tiles_top.json`; scored entries and summaries in `site_lookup.json`; region fields; overlay summaries; site coordinates and numbers inside site names and text; numbers inside quoted v1 ledger text.
- Pages read their numbers from the data files and print the `number` string from this file.
- Citation years (1900 to 2099) in source strings are not treated as numbers.

### `MANIFEST.csv`
- Lives at `data/MANIFEST.csv`, not in `public/data/`. Columns `path`, `bytes`, `sha256`, sorted by path.
- Covers every file under `public/data/` and `data/reference/sites.csv`. Does not list itself. Written last by `make_data`.

## Claims check (CI)

`scripts/check_claims.py` fails, listing every violation, when:
- `claims.csv` differs from what the data files produce, or a claim's hash for a repo file is stale.
- A banned word appears in data text or in page source under `src/app`, `content/` or static `public` text.
- A number appears in data text or page text with no row in `claims.csv`.
- The E32 sentence differs from `docs/E32.txt` anywhere.
- `data/MANIFEST.csv` disagrees with a file, or a file is missing from it.

Not excluded from the scan: everything site-facing. Excluded: `data/banned_words.txt`, `docs/`, `data/reference/*.md`, `scripts/`.

## Which page reads which file

| File | Pages (provisional) |
|---|---|
| `sites.json`, `site_lookup.json` | sites list, site detail |
| `tiles_top.json`, `overlays/*` | candidates, map |
| `regions.json` | regions, map |
| `metrics.json`, `ledger.json` | results, failures, method, home |
| `claims.csv`, `MANIFEST.csv` | CI only |

## Size budget

| File | Limit | Today |
|---|---:|---:|
| `sites.json` | 100 KB | 53 KB |
| `site_lookup.json` | 300 KB | 162 KB |
| `tiles_top.json` | 400 KB | 301 KB |
| `overlays/<target>.png` | 2 MB each | under 0.45 MB |
| `regions.json` | 150 KB | 72 KB |
| `metrics.json` | 100 KB | 74 KB |
| `ledger.json` | 60 KB | 23 KB |
| `claims.csv` | 3 MB | 2.1 MB |
| all of `public/data/` | 8 MB | 3.9 MB |

The build fails if a limit is exceeded. No file approaches 50 MB.

## Not in v1 outputs

- Per-tile family scores for slope, roughness and relief.
- A gazetteer (place names for regions). Blocker.
- Source URLs for the site CSV rows.
- A percentile among all land tiles (gated-out tiles have no score); v1's gated-tile percentile is used.
- Any Moon temperature, composition or thermal inertia score; any Mars water, silica, dust or temperature score.
