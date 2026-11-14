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
- Serves (a), (b), (c). Read by site list and `/sites/<slug>` pages. 120 sites (100 known, 20 candidate), about 160 KB, limit 250 KB.
- Source (B13): the Supabase edit store, `public.sites`, exported by `scripts/export_sites.py` to the committed snapshot `data/reference/sites_export.json` (every column except `id`, `notes` and `created_at`, sorted by body and slug; its sha256 is in `data/MANIFEST.csv`). `make_data` refreshes the snapshot when `SUPABASE_URL` and a key are set (environment or a local `.env`), and otherwise uses the committed snapshot, so a clean clone rebuilds identical files without any key. The deployed site never calls Supabase.
- The table was loaded from `data/reference/raw/GSOP_analog_sites_moon_mars.csv` by `scripts/push_sites_csv.py`; mapping decisions are in `docs/sites_mapping.md`. If no snapshot exists the build falls back to the CSV through the same mapping code. The build checks the snapshot: a banned word in a public text column, a duplicate (slug, body) or a missing coordinate stops it.
- Keys are never printed or committed. The exporter uses the read-only anon key when present and passes keys to curl through stdin. The LLM score columns are not in this table (they live in `sites_llm_raw`, which the anon key cannot read), and the exporter refuses to run if a score-like column ever appears.
- Fields: every column of `public.sites` except `id`, `notes` and `created_at` (the table also has an `unsure` flag, passed through): `slug`, `list` (`known` or `candidate`), `name`, `body`, `country`, `lat`, `lon`, `elevation_m`, `why_analog`, `key_differences`, `experiments_done`, `experiments_possible`, `how_to_modify`, `year_first_used_as_analog`, `status`, `sources_ok`, `source_note`, `origin`, `coord_flag`, `coord_source`, `source_url_1` to `source_url_3`, `v1_used`, and the empty columns `kind`, `analog_of`, `region`, `summary`, `terrain_geology`, `climate`, `parameters_matched`, `access_and_facilities`, `hazards` (all `null`).
- Added by this build: `id` (build key, slug plus body; the same slug can appear once per body), `v1_match` (`{site_id, km}`).
- `v1_used`: the table value when it is set, otherwise filled by the coordinate rule. It is `true`, `false` or `null` (unknown). `true`: within v1's match radius of a v1 site run for that body. `null`: near a v1 site but not matching, or v1 ran that site for the other body only. `false`: beyond v1's exclusion distance of every v1 site.
- Known rows are our reference list. Candidate rows are LLM suggestions: not in our reference list, not used for distances or the region drop rule.
- The CSV has no source URLs, so `sources_ok` is `false` and `source_note` reads "no sources in CSV". The two-source rule from the task was relaxed by instruction.
- All descriptive text is labelled "teammate-written, unreviewed" (`meta.text_label`). Numbers inside names and text get claims rows that cite the CSV.
- The CSV's similarity numbers, Monte Carlo bands, gate labels, rankings and nearest-site columns are not published.

### `site_lookup.json`
- Serves (a), (b), (c). Read by site detail and list pages. 600 entries, about 190 KB, limit 300 KB.
- `meta.label`: "Descriptive lookup of stored v1 scores at reference sites. This is not a test."
- Rule for site to tile: v1's own. The best-scoring tile that passed the gates within the match radius (read from v1's `run.yaml`).
- Percentile: v1's own, `100 * (tiles with a lower score) / (tiles that passed the gates in that view)`. Checked against v1: Haughton and Mars Desert Research Station reproduce v1's stored values to every digit.
- Entry per site and view: `status` (`scored`, `gated_out`, `missing_data`, `no_land_tile`), and for `scored`: `tile_id`, `km_to_tile`, `score`, `percentile`, `top5_in_90pct_runs`. Other statuses carry `reason` and no score.
- `summary_by_view`: per view, `v1_used_true` and `v1_used_false` each with `n` (sites with a percentile), `n_group` (sites in the group) and `median_percentile`; `v1_used_unknown` with counts only.
- Entries cover all 120 sites. Summaries cover known sites only.
- Today (120 sites): 426 scored, the rest gated out, missing data or no land tile.

### `tiles_top.json`
- Serves (a). Read by candidates table and map. 3 views, 1,500 tiles, about 450 KB, limit 600 KB.
- Decided for B12: top 500 tiles per target. The base profile of each target is listed; the other profiles stay in `site_lookup.json` and `metrics.json`. Order: flagged first, then Monte Carlo median, then tile id.
- View fields: `target`, `profile`, `body`, `confidence`, `illum_match_family`, `n_gated_tiles`, `n_top5_in_90pct_runs`, `source_file`, `sha256`, `tiles`.
- Tile fields: `tile_id`, `lat`, `lon`, `score`, `mc_median`, `mc_p05`, `mc_p95`, `freq_top5`, `top5_in_90pct_runs`, `illum_match`, `in_india`, `nearest_reference_site`, `km_to_nearest_reference_site`.
- Claims rows exist for the fields pages display: `lat`, `lon`, `score`, `mc_p05`, `mc_median`, `mc_p95`, `km_to_nearest_reference_site`.
- Family scores: v1 stores only the lighting family per tile (`illum_match`). Slope, roughness and relief family scores per tile are not in v1 outputs and are omitted.
- `in_india` comes from v1's own flag (Natural Earth outline, not an official map).

### `overlays/<target>.png`, `<target>.json`, `legend.png`, `legend.json`
- Serves (a), (b). Read by the map page. Three PNGs of 0.3 to 0.45 MB each, limit 2 MB.
- Base profile, one per target. Equirectangular, west -180 to east 180, south -55.4 to north 82.9, 3600 by 1383, 0.1 degree pixels. Transparent means no v1 score.
- Colour scale, resampling and known artifacts are in `docs/DATA_NOTES.md`.

### `regions.json`
- Serves (a). Read by regions page and map. 20 regions, limit 150 KB.
- Cluster rule: tiles flagged top 5% in at least 90% of runs (v1's flag), base profile of each target, joined by 8-neighbour adjacency, wrapping at the date line.
- Parameters set in this build, each listed as a fact with its source script: minimum 100 tiles; drop clusters within 100 km of any known reference site (v1's own `min_distance_km`); keep the top 10 regions per target, ranked by median Monte Carlo score (decided for B12).
- Result: Shackleton rim 10, Jezero 10, Connecting Ridge C1 0 (its largest flagged cluster is below the minimum). Counts before the top-10 cut are in `meta.by_view`.
- Fields: `id` ("Region NN", stays the ID), `target`, `profile`, `body`, `confidence`, `n_tiles`, `area_km2`, `centroid_lat`, `centroid_lon`, `bbox`, `median_score`, `median_mc_median`, `km_to_nearest_reference_site`, `nearest_reference_site`, `n_tiles_in_india`, `place`, `status` ("Unreviewed"), `caveat`.
- `place` (decided for B12): `{name, feature_class, relation, distance_km, source}`. The name is the Natural Earth desert, plateau or range the centroid lies in (`relation: inside`, distance 0), else the nearest such region within a near distance (`near`, 200 km, a build choice), else the nearest populated place (`nearest populated place`). Distance is approximate. Source layers and hashes are in `data/reference/raw/NATURAL_EARTH.md`.
- `n_tiles_in_india` uses a point-in-polygon test against v1's outline; the test agrees with v1's own flags on its top-500 file.

### `controls.json`
- Serves (c). Read by the Honest Map. 4 controls, under 20 KB.
- The negative controls v1 used, with coordinates and the stored result per run (`moon`, `mars`): `status`, `rank_pct` when scored, `reason` when gated out, `coordinates_confirmed`.
- Source: `results/<run>/validation.json`. Claims rows exist for latitude, longitude and each stored percentile.
- Two controls scored far above the pre-registered maximum on the Moon run. The map shows controls in red.

### `v2.json`, `site_measurements.json` and `public/img/sites/` (optional, issues B16 and C8)
- Serves (b), (c), (d). Read by the Ledger page (v2 section) and the per-site pages (measured evidence). Every input is optional: the build and the site work with all of them absent, with some present and with all present (tests: `python3 -m unittest discover -s scripts/tests`, run in CI).
- Inputs come from `AnayDhawan/sim`: `python3 scripts/sync_v2.py` copies whatever exists on `main`, `data/thermal-refs` and `data/site-evidence` into `data/v2/` with the same paths, and records branch, commit and sha256 in `data/v2/SOURCES.csv`. Nothing is edited or invented. Every file under `data/v2/` is in `data/MANIFEST.csv`.
- Expected inputs: `runs/v2/metrics.json`, `ledger.json`, `claims_v2.csv`, `claims_c.csv`; `PREREG_*.md` with `prereg_*.sha256`; `data/reference/thermal_refs.csv` and `thermal_refs_files.csv`; `data/evidence/site_measurements.csv`, `ledger_c.json`; `public/img/sites/` (JPEG chips and `credits.json`); `docs/refs_limits.md`, `evidence_limits.md`, `data_resources.md`.
- `v2.json`: `run_completed` (true only when both `runs/v2/metrics.json` and `ledger.json` exist), `status_text` ("v2 run not completed" otherwise), `inputs` (every expected file with present flag, bytes and sha256), `preregistrations` (per `PREREG_X.md`: title, sha256 of the LF-normalised document, the hash recorded in `prereg_x.sha256`, whether they match, and a deviations file when present), `thermal_refs` (rows from `thermal_refs.csv`, or `null`), `limits_docs`, `has_site_measurements`, `n_chip_files`.
- Thermal rows carry `status`: `value` (with `display`), `not_covered`, `empty` or `label`. Display rule: four significant digits, counts as integers. A `not_covered` row has no number. Claims ids are `v2.thermal.<site>.<layer>.<stat>`.
- The `claims_v2.csv` and `claims_c.csv` files are copied but not merged: this build writes its own claims rows from the data it shows, so each shown number still has one row in `claims.csv`.
- Gate results and v2 metrics are not shown yet. When the v2 ledger arrives its literal statuses (PASS, FAIL, NOT TESTED) will be shown; until then the page says "v2 run not completed". Nothing is estimated.
- `site_measurements.json` exists only when `site_measurements.csv` is present, in the layout fixed by `runs/v2/PREREG_C.md` section 4 (a missing required column stops the build). Rows are grouped by site id, matched on site name and body. A null stays as a null with its note and reads "not measured" on the page. Rows with `page_ok` false are never shown (approximate coordinates keep only the larger radius, with a caveat). Display rule: three significant digits. Claims ids are `v2.evidence.<site id>.r<radius>.<dataset>.<variable>.<stat>`, plus `v2.evidence.radius.<radius>`.
- Chips are copied to `public/img/sites/<slug>.jpg`; the page shows the chip with the credit string from `credits.json`. A stale output is removed when its input is removed.
- The limits documents (`docs/refs_limits.md`, `evidence_limits.md`, `data_resources.md`) are stored in `v2.json` under `limits_docs` as blocks (headings, nested bullets, paragraphs, inline code), when they exist. The Methods page shows them. Every number in them gets a claims row, `v2.doc.<id>.b<block>.n<index>`, that cites the document and its hash. A missing document is reported as "not available yet".

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
- Columns: `claim`, `number`, `source_file`, `sha256`. Sorted by `claim`. 13,294 rows, 2.5 MB, limit 3 MB.
- Rows come from: every `meta.facts` entry; numeric metrics; per-tile values in `tiles_top.json`; scored entries and summaries in `site_lookup.json`; region fields; overlay summaries; site coordinates and numbers inside site names and text; numbers inside quoted v1 ledger text.
- Pages read their numbers from the data files and print the `number` string from this file.
- Citation years (1900 to 2099) in source strings are not treated as numbers.

### `MANIFEST.csv`
- Lives at `data/MANIFEST.csv`, not in `public/data/`. Columns `path`, `bytes`, `sha256`, sorted by path.
- Covers every file under `public/data/`, `data/reference/sites.csv` and `data/reference/raw/` (the site CSV and the Natural Earth files). Does not list itself. Written last by `make_data`.

## Claims check (CI)

`scripts/check_claims.py` fails, listing every violation, when:
- `claims.csv` differs from what the data files produce, or a claim's hash for a repo file is stale.
- A banned word appears in data text or in page source under `src/app`, `content/` or static `public` text. The E32 sentence is allow-listed, because it must stay verbatim.
- A number appears in data text with no row in `claims.csv`.
- Page source holds a typed number in prose. Pages must print numbers from `claims.csv`; class names and code are not scanned.
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
| `sites.json` | 250 KB | 162 KB |
| `site_lookup.json` | 300 KB | 193 KB |
| `tiles_top.json` | 600 KB | 440 KB |
| `overlays/<target>.png` | 2 MB each | under 0.45 MB |
| `regions.json` | 150 KB | 25 KB |
| `metrics.json` | 100 KB | 74 KB |
| `ledger.json` | 60 KB | 23 KB |
| `v2.json` | 250 KB | 134 KB |
| `site_measurements.json` | 2 MB | absent |
| `claims.csv` | 3 MB | 2.1 MB |
| all of `public/data/` | 8 MB | 3.9 MB |

The build fails if a limit is exceeded. No file approaches 50 MB.

## Not in v1 outputs

- Per-tile family scores for slope, roughness and relief.
- Source URLs for the site CSV rows.
- A percentile among all land tiles (gated-out tiles have no score); v1's gated-tile percentile is used.
- Any Moon temperature, composition or thermal inertia score; any Mars water, silica, dust or temperature score.
