# Data notes: v1 intake (Phase B)

Internal notes on what the v1 results zip holds. Nothing here is site text. Everything below was read from the files; nothing was rerun.

## Inputs

| Input | Where | sha256 |
|---|---|---|
| v1 results zip | `gsop_v1_results_2026-11-14.zip` (repo root, git-ignored via `*.zip`) | `0c634823629cb3e1719feafd053f99cc3eea1aabc974316fa1a7fefcf7a4076a` |
| Site CSV (LLM-written) | `data/reference/raw/GSOP_analog_sites_moon_mars.csv` | `9052ef80275bef814feee0c4830ad81492d0f48aa2dff2bee8902065c116f80f` (same content as the copy first received, `86439f85…`; only line endings differ) |

- Zip size: 287,366,854 bytes compressed; 366 entries (365 data files plus `FILES.sha256`); 545,140,228 bytes of data when unpacked.
- Unpacked to a scratch directory outside tracked paths. The raw zip and CSV were not modified.
- Only one zip and one CSV exist in the repo, so there was no ambiguity about which inputs to use.

## Hash check

- The zip contains its own hash list: `gsop_v1/FILES.sha256` (365 lines, sha256, one per data file).
- Result: 365 of 365 files match. No file is listed but missing. No file is present but unlisted.
- The 41 files named in the three `results/*/export/MANIFEST.json` files also match their stated sha256.
- `data/processed/MANIFEST.json` lists 5 files; not separately re-checked, they are covered by `FILES.sha256`.
- The zip itself has no externally published hash to compare against. The sha256 above is the one we recorded.
- Run provenance (all three runs): `git_commit` a7d96d9, `config_hash` ab39ae5cf2, `master_seed` 20261114, 2,000 Monte Carlo runs. Earth feature file hash `df31e93c...0182a966` (full value in `results/*/run_meta.json`).

## Real layout

Root inside the zip is `gsop_v1/`.

- `FILES.sha256`: hash list (365 entries).
- `config/` (10 YAML files): `run.yaml`, `targets.yaml`, `weights.yaml`, `features.yaml`, `gates.yaml`, `known_sites.yaml`, `ledger.yaml`, `open_data.yaml`, `earth_layers.yaml`, `purposes.yaml`.
- `data/processed/` (6 files, 134.7 MB): `earth_features_6km.parquet` (3,972,955 land tiles by 18 columns), `grid.json`, `earth_coverage.json`, `targets_moon.parquet`, `targets_mars.parquet`, `MANIFEST.json`.
- `docs/` (11 Markdown files) and `docs/evidence/` (3 CSV, 1 JSON, 1 PDF). Includes `DECISIONS.md`, `PROVENANCE.md`, `SPEC.md`, `UNVERIFIED.md`, `RESULTS_SCHEMA.md`.
- `results/moon/`, `results/moon_lat20-40/`, `results/mars/`, each with:
  - `gates__<profile>.parquet` and `.json`: gate code per land tile.
  - `<target>__<profile>/` (8 files): `base_scores.parquet`, `mc_summary.parquet`, `mc_counts.npz`, `summary.json`, `alt_weight_checks.json`, `convergence.json`, `discovery.json`, `ml.json`.
  - `validation.json`, `run_meta.json`, `export/`, `.done/` (job markers).
  - `export/` holds `candidates__<target>__<profile>.json` (top 500 each), `convergence__*.json`, `fidelity.json`, `index.json`, `validation.json`, `MANIFEST.json`.
  - `results/moon_lat20-40/compare_with_full.json` compares the latitude-band run with the full Moon run.
- `site_data/` (57 files): CSV and GeoJSON of the top 500 tiles per view, `india_*.csv` (top 100 tiles inside India per view), `india_boundary_naturalearth_ind_10m.geojson`, `limits_<run>.json`, `validation_summary_<run>.json`, `run_summary.json`, `README_site_data.md`.

### Runs, targets and profiles

- Moon: targets `connecting_ridge_c1` and `shackleton_rim`; profiles `base`, `landing_mobility`, `power_night` (6 views). `ice_resources` was not run (columns missing).
- Moon latitude 20 to 40 run: same 6 views, a band check only.
- Mars: target `jezero`; profiles `base`, `ice_resources`, `landing_mobility`, `power_night` (4 views). `geology_life` was not run. `arcadia` is unscored (no target data). Confidence is `low` per the wording rules.
- Grid: EPSG:6933, 6,000 m cells, 5,790 columns by 2,448 rows. `tile_id = iy * 5790 + ix`. Tile centre: `x = x0 + (ix + 0.5) * 6000`, `y = y_top - (iy + 0.5) * 6000`, with `x0 = -17367530.445161372` and `y_top = 7342230.136498678` (`data/processed/grid.json`).

## What the brief asked about

| Item | Present? | Where / note |
|---|---|---|
| Per-family scores | **Partly** | Not stored per tile. `base_scores.parquet` has `tile_id`, `score`, `illum_match` only. `illum_match` is the illumination (Moon) or sunlight (Mars) family alone. Slope, roughness and relief family scores per tile are **not in v1 outputs**. Family weights are in each `summary.json`. |
| Per-tile score files | Yes | `base_scores.parquet` per view: every tile that passed the gates (Moon 1,226,294 base; Mars 1,226,654 base). |
| Robust-tile flags (top 5% in at least 90% of runs) | Yes | `robust` column in `mc_summary.parquet`. Count equals `n_robust` in `summary.json` for all 16 views (checked). `mc_summary` holds the flagged tiles plus other top tiles (about 17,000 to 52,000 rows per view). `mc_counts.npz` holds per-tile top 1, 5 and 10 percent run counts for every gated tile. |
| Land mask | **Indirect** | No raster. The land tile set is the `tile_id` column of `earth_features_6km.parquet` (3,972,955 tiles, land share at least 0.5). Gate codes per tile are in `gates__*.parquet`. |
| List of sites v1 used | Yes | `config/known_sites.yaml` (18 entries: 6 primary, 5 secondary, 3 gate tests, 4 negative controls). Per-site results in `results/<run>/validation.json`. |
| Pre-registration hash | Yes | `preregistered_sha256` in `validation.json`. Moon and Moon 20 to 40: `6bdaaf3a0ece49205985363a026287d34b5492291e33e2bf8b4a159c41961d55`. Mars: `2fa168bea9cdcada26a06a0588c7f1c2ee2baf81e2be72097225ebb16064ed69`. Registered 2026-11-14. |
| Gazetteer | **No** | Not in the zip. Only Natural Earth India boundary (admin-0, 1:10m). GeoNames appears once, as the source for one control point's coordinates, not as a dataset. See B10 blocker below. |
| E32 sentence | Yes | Verbatim in `docs/DECISIONS.md` (entry E32, item 8), `site_data/run_summary.json` (`uncertainty_sentence`) and `site_data/README_site_data.md`. All three copies are byte-identical (251 characters, ASCII only). |

## Facts from the brief, checked against the files

| Brief said | File says | Source |
|---|---|---|
| Namib failed control 90.2 | 90.19325708 (rank percentile, Moon) | `results/moon/validation.json`, `negative_controls.namib_sand_sea` |
| Rub' al Khali 75.6 | 75.55875671 (Moon) | same, `negative_controls.rub_al_khali` |
| Mars primary median 61.3 | 61.28835026 (5 scorable primary sites; Lonar gated out) | `results/mars/validation.json` |
| Moon score terrain-only | Confirmed. Moon `illum_match` is at most 0.001 on every tile. With the illumination weight set to 0, top 1% overlap with the base ranking is 1.0 in all 6 Moon views and Spearman is at least 0.99988. | `alt_weight_checks.json`, `base_scores.parquet` |

No mismatches found. Further details the site must carry:

- Moon criteria status (`results/moon/validation.json`): primary median `not_testable` (1 scorable primary site, Haughton, Lonar gated out); negative controls `fail`; gate tests `pass`; all pre-registered criteria together `false`.
- Mars criteria status: primary median `fail` (threshold 90); negative controls `not_testable` (both gated out); gate tests `pass`.
- The latitude 20 to 40 run: Haughton, Amazon, Congo and several secondary sites have `no_gated_tile` (outside the band). Controls still fail (Namib 91.98).
- All three runs carry `provisional: true` (11 site coordinates unconfirmed) and `slope_ground_scale_corrected: false`.

## Concerns about the inputs

- `docs/DECISIONS_SITE.md` and `docs/SUBMISSION_RULES.md` do not exist in this repo or its history, so they were not read.
- The site CSV does not match the schema in the brief and has no source URLs; the two-source rule was relaxed by instruction. See `data/reference/sites_check.md` (B2).
- v1 tile scores exist only for tiles that passed the gates (about 31% of land tiles for Moon). Gated-out tiles have no score.
- The latitude 20 to 40 Moon run covers only part of the globe, so its tile grid differs from the full run.

## Data credits found in the zip

Source: `docs/PROVENANCE.md`, `config/*.yaml`, `docs/DECISIONS.md`, `site_data/README_site_data.md`. Licences are as stated in those files; several rows say "not returned by the API, check the catalog page". The credits record must be completed against the catalog pages before publication.

### Earth

- Elevation: SRTM 90 m v4 from CGIAR-CSI (`CGIAR/SRTM90_V4`), 56 S to 60 N; Copernicus DEM GLO30 (`COPERNICUS/DEM/GLO30_2024_1`) outside that band (DLR/Airbus attribution). `earth_coverage.json` shows both were used. NASADEM (`NASA/NASADEM_HGT/001`) is also listed in provenance.
- Land cover, gates: MODIS MCD12Q1 v6.1 (`MODIS/061/MCD12Q1`), year 2023 or 2024 (provenance gives both; check).
- Vegetation gate: MODIS MOD13A2 v6.1 NDVI.
- Other layers listed in provenance, some unused or dropped: MODIS MOD11A2 land surface temperature, TerraClimate, GPM IMERG, MOD16A2GF PET, NASA ASTER GED, MERRA-2 aerosols.
- Earth air density: NASA Glenn atmosphere model.
- Access route: Google Earth Engine.
- India outline for labels and the India filter: Natural Earth 1:10m admin-0, India point of view, public domain. The zip says this is not an official Survey of India map.

### Moon

- LOLA south-polar DEM and PSR map, NASA PGDA (Barker et al. 2023, PSJ 4:183, doi 10.3847/PSJ/acf3e1; data doi 10.60903/gsfcpgda-lola-spole).
- Target site data: Glaser et al. 2018 (lit and shadow statistics for Connecting Ridge C1 and Shackleton rim).
- Diviner products (LRO): named in provenance for temperatures, roughness checks and silica; not used in the score (not available at the pole).
- Literature in the ledger: Paige et al. 2010 (Science 330:479), Liu 2025 weights, NASA Moon fact sheet, NASA SVS 4893.

### Mars

- MOLA DEM 463 m (USGS Astrogeology, CC0).
- THEMIS thermal inertia of Jezero, Zenodo record 4931348 (Edwards and Buz 2021, CC BY 4.0). Not scored.
- Mars Climate Database v6.2 (LMD). Not scored.
- NASA Mars fact sheet (solar constants); NASA Glenn Mars atmosphere model (air density).
- Jezero centre: Grant 2018.
- SWIM ice consistency and TES dust cover index were checked and not scored.

## Concerns for later tasks

- B10 gazetteer: none in the zip. Blocker until Anay or Yash names one. Natural Earth populated places would be consistent with the boundary credit already in the zip, but that is a choice for them.
- B8 percentile: v1 stored rank percentile among gated tiles, not among all land tiles. The build uses v1's definition (checked against v1's stored values).
- The word "robust" is a v1 field name (`robust` flag). It is also on the CLAUDE.md list of words to avoid in prose. Use it only as a code identifier; prose says "flagged tiles".

## Map overlays (B6)

Built by `scripts/gsop_data/overlays.py`. One PNG per target, base profile, from `base_scores.parquet`.

- Targets: `connecting_ridge_c1`, `shackleton_rim` (Moon), `jezero` (Mars, low confidence).
- Projection: equirectangular, EPSG:4326, west -180 to east 180, south -55.4 to north 82.9 (union of the three targets), 0.1 degree pixels, 3600 by 1383.
- Resampling: nearest neighbour. Each output pixel centre is converted to EPSG:6933 and takes the score of the tile it falls in. Nothing is interpolated or averaged, so no value is created that v1 did not store. Pixels are finer than a tile at high latitude and coarser near the equator.
- Colour scale: 5 stops, linear, viridis-like (#440154, #3b528b, #21908c, #5dc863, #fde725) mapped onto the fixed range 0 to 100 (the documented score range). Palette index 1 to 255; index 0 is transparent.
- No data: transparent. This covers water, tiles that failed a gate, and tiles with missing data. It does not mean a low score.
- Scale is shared across targets, so colours compare directly, but observed scores sit well below the top of the range (Moon base maximum about 70).
- Sidecar JSON per overlay holds bounds, size, observed min, median and maximum from `summary.json`, and the limits list.
- Artifacts that come from v1 data, not from this build: a thin line at 60 N (terrain source changes from SRTM to GLO30) and a block edge over Siberia (same cause, see E32 item 10). Large transparent areas (Amazon, Congo, much of Europe and India) are tiles the vegetation gate removed.
- PNG writing uses fixed compression and no metadata chunks, so output is byte-identical between runs.

## Appendix: file inventory

Every file in the zip (path, bytes, sha256). Matches `gsop_v1/FILES.sha256`.

| Path | Bytes | sha256 |
|---|---:|---|
| `config/earth_layers.yaml` | 2668 | `7ba1a19a68028131d2b953db5d99b98cc8a9e8c70c2bb6fe23a9685380badcf9` |
| `config/features.yaml` | 6362 | `c4ffab194c3f7fd3769c6c30a5d81585f83e1417a7399065ef6ef7212efde183` |
| `config/gates.yaml` | 658 | `76a0d38518620a19c1e896afb4a6411827829d2d3b367ba74345ff5a8052ac5f` |
| `config/known_sites.yaml` | 6890 | `7efcfe9806ebfa19874e1153122c795b254bce7e89020ebff4603c86af51b9ea` |
| `config/ledger.yaml` | 8483 | `dc07b3129af761928f992d3d503f1978f56467a91daab26024d0433e431edf68` |
| `config/open_data.yaml` | 1809 | `4e020784029635595126334d09fc26ce522ebd8a7631de219dec2d0946914ff3` |
| `config/purposes.yaml` | 892 | `f125a0fe6e07e634021357bbb505f7339c6d5b29897e906342a3376490a3e513` |
| `config/run.yaml` | 2840 | `b34a192b231c0b1e0d6af274df66e029d70cb1e6abbced26c7a3925d62540b56` |
| `config/targets.yaml` | 5478 | `a9b02cc6e500f4bbe8d4e9709af669946b56c1818faed625c579319fcd37cd0a` |
| `config/weights.yaml` | 2964 | `1aa16ef14258779d3b2f696eb22656869b5aa2780f781cf35467d25acaff7a47` |
| `data/processed/MANIFEST.json` | 710 | `c4a6592227a4ce2344a3c26c652491a863ad48e3341ebc5b7dfc52810afe1d86` |
| `data/processed/earth_coverage.json` | 752 | `8a53830089f63b94fff82da3a2737f2d957016709d1c6ca65c77581dee6b88c7` |
| `data/processed/earth_features_6km.parquet` | 134735723 | `df31e93c4034ecb908a2d378ab2335d817e8751b32616e135de8febc0182a966` |
| `data/processed/grid.json` | 176 | `91d6e3af116099a62224db621e5674015e4f04e72c9482bc3908afd5bc404f9b` |
| `data/processed/targets_mars.parquet` | 6439 | `f348e7b9333ea2bb129373bcebdf1f9b4b8777761f02d6940b8f423512ddca7b` |
| `data/processed/targets_moon.parquet` | 5621 | `36f35332dcb51b1041c7c2f4302ab4bc4fc9738c8911b261de5fc263a64dcad5` |
| `docs/DECISIONS.md` | 18330 | `f25c17dab5b4778de3c1bdba047df7efdcf041be41eff0618ebfb7c2f351aa91` |
| `docs/EE_COST.md` | 47207 | `7e06685d0e5f3d89501ce106127348b038214aa7c72faf67aa825c277b797e0d` |
| `docs/OPEN_ITEMS_TRIAGE.md` | 12439 | `ff3bab01140ef58fadf73540901b4c80e4a961415b8f0edbacbaa04510da2be6` |
| `docs/PERF.md` | 8198 | `7491882b4988a98177b6189a0f5b0982fd053a6eaf9c38c7a48ecda38195ddf4` |
| `docs/PROPOSAL_candidate_climate_rescoring.md` | 4215 | `08dc0dcb1220a9ff4aa339d849382353528ded710e096cc7aa2a20297f1236c2` |
| `docs/PROVENANCE.md` | 27969 | `de9b29b8eca7f4bbe908234607bdbe3b348d774707b131dac36fddce90d70e41` |
| `docs/RESULTS_SCHEMA.md` | 3830 | `7a8a0a72b319a1c20025cb6a0600c60f54810205ff0e0c2e3df1852d15e0d0bc` |
| `docs/RUNBOOK_SUNDAY.md` | 7742 | `9e394c9f11a2922be5c9c417bec59394d5102d83370701e5dcbce887c83c8c8d` |
| `docs/SPEC.md` | 42415 | `cb2852923a05355acb1f0790fa1e35f87c831e690f12fe4a7465b2a6033540ed` |
| `docs/UNCERTAINTY_SOURCES.md` | 4426 | `bec0f2189945433db33acfd3b3eaf55565e02ea3a502111151ca23c3433b1d1a` |
| `docs/UNVERIFIED.md` | 27233 | `007e03982cc85e33a2e77052f994d2c722b86a592f0aaeb7d0962336254e07e9` |
| `docs/evidence/mars_evidence_shiven_2026-11-14.csv` | 3735 | `442a1084ac04206f56669e58cf87bb6e87359261859c11abad6dcf3a21bb1715` |
| `docs/evidence/mcd_v6_2_jezero_tsurf_2026-11-14.csv` | 20338 | `cd4f5705bdbd68dca463a3bab0d5794f4bdba00fa27622969dd8e8a358525b53` |
| `docs/evidence/mcd_v6_2_jezero_tsurf_2026-11-14.meta.json` | 1477 | `2992d9e4d4223866e2b5dfd23ec8e5abe207b26b975e65ee8c389615744b831f` |
| `docs/evidence/moon_checks_diviner_roughness_ledger_2026-11-14.pdf` | 367150 | `3ed188bbd0c11897c69a5b4b84d0da60570212b2c4c583bf87d01db94896a4dc` |
| `docs/evidence/moon_evidence_vihaan_2026-11-14.csv` | 4925 | `2a0f4e92ee83ed9afae02d74a05c1a7cb57be75d618f4c2b3ab62d8a02006032` |
| `results/mars/.done/discover__jezero__base.json` | 274 | `e7e4f8d36fef06687e5d5e21f778caa31fadc705d03818f523f5c991bab08a0c` |
| `results/mars/.done/discover__jezero__ice_resources.json` | 284 | `d916d29e080d6aabbafc893b9df35d3613bd8bd0a5b5f4c82de56a6f1d7ca84d` |
| `results/mars/.done/discover__jezero__landing_mobility.json` | 287 | `6bf47a6b66c932a569ccd2120d9faa3dc7168aa5ddc8c7c5e2e2c96156593ccd` |
| `results/mars/.done/discover__jezero__power_night.json` | 282 | `3ab0585109c84c9ce3d420649668636b324728f6278ba2c94257e6b07740e52f` |
| `results/mars/.done/gates__base.json` | 263 | `1311b31eb56ed0c2f31adcd1fb1858669937e797e789cd83fd9ae0688e597004` |
| `results/mars/.done/gates__ice_resources.json` | 271 | `be153810b1326ae32ea72e879322351b3cd8f3f061a8ea9c9c7ad8db9cb18b12` |
| `results/mars/.done/gates__landing_mobility.json` | 275 | `ea6b34195506ad9d9012ba7d5f8c3f7a6a279e81d85df403033ef48432963d3e` |
| `results/mars/.done/gates__power_night.json` | 270 | `9133d5302cdebe75a5793f4db256d943d5aef56af9118c4903804ed9c659936b` |
| `results/mars/.done/ml__jezero__base.json` | 268 | `f1ed96a9d867292aac68d7eae626a36ecf687f5f9257d621a86fd6cabfaf66e2` |
| `results/mars/.done/ml__jezero__ice_resources.json` | 277 | `22f23b04039fe43c7e8790f19abc382f3378dd8e39d6e953958f0f45996e0c91` |
| `results/mars/.done/ml__jezero__landing_mobility.json` | 280 | `81061ca9d6c70cec438347d84fbcb5dc30cf4e4dbd063025bff1afa9fee500d0` |
| `results/mars/.done/ml__jezero__power_night.json` | 275 | `9df591d3050964c49fd96b43d7156f4f4454f4b1117619bd75f566f788aecb90` |
| `results/mars/.done/score__jezero__base.json` | 297 | `7dc41e2e5a1c1b79a503cf96d741d0f5b296e0f6de326b12ee9985ac221d1c31` |
| `results/mars/.done/score__jezero__ice_resources.json` | 307 | `6d334d8c78487ac1d2e136d500591e5ba790d657a4bce3e180c962ba540dba7b` |
| `results/mars/.done/score__jezero__landing_mobility.json` | 310 | `fe847bf08da07e55f5ed202c2190668eeb6bd9856ff7f1bd39fa3681f2b581bc` |
| `results/mars/.done/score__jezero__power_night.json` | 305 | `efb47a59111c440d8a20624b78550b2f4c1d7486ec9d505adaebde88aa890a66` |
| `results/mars/.done/simulate__jezero__base.json` | 301 | `bc0ba07a05d6d9cbc9fa5bb9d1fec29e4153e721a67cb8b1315b9e239b32bc9c` |
| `results/mars/.done/simulate__jezero__ice_resources.json` | 310 | `7df471eec2e3f77a6f948e6a60759bd1c7ac8a9930061753e3c0708a74491352` |
| `results/mars/.done/simulate__jezero__landing_mobility.json` | 313 | `3b20391c5925b088fff04b2002b2754eaaa7774772991db94f613ef6ef7d4e14` |
| `results/mars/.done/simulate__jezero__power_night.json` | 307 | `3159ded077b17022ee4cd80eb263535392dfa29cc77f06e3b52cf8b3a1b5e232` |
| `results/mars/.done/validate__body.json` | 265 | `a917991ff78f647c4909e8f27991d025e2d372d2c19e2f0e4e8dc01ceceb3328` |
| `results/mars/export/MANIFEST.json` | 1613 | `49b5163347c1ef37c2da523d1c37d217f275b16f8ec48ae7f5dbfcdcb3e8f1d6` |
| `results/mars/export/candidates__jezero__base.json` | 187635 | `8abd599680d5d2a3a424f505f4bda1ca537028487efcde1f9c550c01965c0cab` |
| `results/mars/export/candidates__jezero__ice_resources.json` | 187644 | `e39064a2bf39998df2196599052410f2c62509a0f98768ae86fb491afd3a8f0d` |
| `results/mars/export/candidates__jezero__landing_mobility.json` | 187605 | `48f1ac149493cd29aaa2de0893a7eb7b0466713745389fd93be71e437c09a347` |
| `results/mars/export/candidates__jezero__power_night.json` | 187579 | `76f8bc3555e965b32bcaab307289747bec0cef58008335ee40c51024d59ca972` |
| `results/mars/export/convergence__jezero__base.json` | 483 | `dd0e25b1ac918917ecd889ca2ba55ac2d3149d098acc2cad32e57f2c595907cb` |
| `results/mars/export/convergence__jezero__ice_resources.json` | 483 | `dd0e25b1ac918917ecd889ca2ba55ac2d3149d098acc2cad32e57f2c595907cb` |
| `results/mars/export/convergence__jezero__landing_mobility.json` | 482 | `16e531f569c11a0db4262bf9d13d806e8193dd3451605e10211c832ddda26eff` |
| `results/mars/export/convergence__jezero__power_night.json` | 484 | `c2ea125c962d0f9624b6363d64631ad9f558e28bf12e5bef28e7e41cff1d06c5` |
| `results/mars/export/fidelity.json` | 8751 | `c3334a19782a0f1247dcd1475f228ae2c778a49cc79969534cad4a9db3a913e2` |
| `results/mars/export/index.json` | 2132 | `400d2c87a7146982cd5798f26a6f00f253c7b93794b665108808b212d4544e12` |
| `results/mars/export/validation.json` | 9602 | `7df4fe948dda1ae84c488f537e97d26b6f9c582be43be19cfbf508ee286e9a68` |
| `results/mars/gates__base.json` | 205 | `9591e8756e4a3244262b3b5485b4c4fde26a4a80affc8f162761591e80c8c1ff` |
| `results/mars/gates__base.parquet` | 17239096 | `10d775783b762b2845727ad5a063c8cfe8a38f5c6fbbe4b5d75e7ce58f89b92d` |
| `results/mars/gates__ice_resources.json` | 214 | `44346e4ac880b56382a8e3a453d35fa18aaad2e3c9d7006aabb0facf1b2357c2` |
| `results/mars/gates__ice_resources.parquet` | 17239096 | `10d775783b762b2845727ad5a063c8cfe8a38f5c6fbbe4b5d75e7ce58f89b92d` |
| `results/mars/gates__landing_mobility.json` | 240 | `c9cc5c9b864344d32696d144dde0f43380d78f36055453d2917c0cd819d4e905` |
| `results/mars/gates__landing_mobility.parquet` | 17251440 | `0dd955e389bfe31de7d6c85be4ced18276bfa1fd86c95f50f148bfc4cdabfde8` |
| `results/mars/gates__power_night.json` | 212 | `6bd8d6f6f1f35341599ee92c0fa2c4d7e87cd72cec36d5b77bc5a09fb33ed1e3` |
| `results/mars/gates__power_night.parquet` | 17239096 | `10d775783b762b2845727ad5a063c8cfe8a38f5c6fbbe4b5d75e7ce58f89b92d` |
| `results/mars/jezero__base/alt_weight_checks.json` | 415 | `eedb1962dfa560b9ea7ea3a211161ef47518d6ce19ae5351d0b87cdc33ad9c9a` |
| `results/mars/jezero__base/base_scores.parquet` | 10804056 | `628ac6fd096900cc8a17496c915a66cde9c6655bd5f1d926a437bfc7e58ca9ac` |
| `results/mars/jezero__base/convergence.json` | 483 | `dd0e25b1ac918917ecd889ca2ba55ac2d3149d098acc2cad32e57f2c595907cb` |
| `results/mars/jezero__base/discovery.json` | 26688 | `2c2afa9d9f17253261af00fd29e8fd82964642fa55f51bc45bad917cc7e14a02` |
| `results/mars/jezero__base/mc_counts.npz` | 6109220 | `3ef1215a62d686c6f7086c785015c132a4a2b04eff306a0b905d5fbec687c4fa` |
| `results/mars/jezero__base/mc_summary.parquet` | 3411185 | `6c8d858809e87d7da6e255dc38581f8be8eb7ce4293e2c2a1ebc092a3bf11809` |
| `results/mars/jezero__base/ml.json` | 1491 | `1701dfd5aef2fb18ab1e45a956680b049778dd88669c07ec611f1907cb16b90b` |
| `results/mars/jezero__base/summary.json` | 2994 | `b64770d262ad669e88ff8bf35c3a22c388e9c998c78d59fe0be5586fbd493b3a` |
| `results/mars/jezero__ice_resources/alt_weight_checks.json` | 415 | `eedb1962dfa560b9ea7ea3a211161ef47518d6ce19ae5351d0b87cdc33ad9c9a` |
| `results/mars/jezero__ice_resources/base_scores.parquet` | 10804056 | `628ac6fd096900cc8a17496c915a66cde9c6655bd5f1d926a437bfc7e58ca9ac` |
| `results/mars/jezero__ice_resources/convergence.json` | 483 | `dd0e25b1ac918917ecd889ca2ba55ac2d3149d098acc2cad32e57f2c595907cb` |
| `results/mars/jezero__ice_resources/discovery.json` | 26688 | `2c2afa9d9f17253261af00fd29e8fd82964642fa55f51bc45bad917cc7e14a02` |
| `results/mars/jezero__ice_resources/mc_counts.npz` | 6109220 | `3ef1215a62d686c6f7086c785015c132a4a2b04eff306a0b905d5fbec687c4fa` |
| `results/mars/jezero__ice_resources/mc_summary.parquet` | 3411185 | `6c8d858809e87d7da6e255dc38581f8be8eb7ce4293e2c2a1ebc092a3bf11809` |
| `results/mars/jezero__ice_resources/ml.json` | 1491 | `1701dfd5aef2fb18ab1e45a956680b049778dd88669c07ec611f1907cb16b90b` |
| `results/mars/jezero__ice_resources/summary.json` | 3003 | `b191083b22a8aceefc79123805367039b0344ee4310ba684fba83896ae7da244` |
| `results/mars/jezero__landing_mobility/alt_weight_checks.json` | 415 | `ee53c184fcd4f8176a37e0315cc52128702dc083eda4eb9daf4a1f87ad613b15` |
| `results/mars/jezero__landing_mobility/base_scores.parquet` | 10730329 | `b8746bf2ff32d917e5d80b53ba0430d1aa4834c0017b4fc86618c8a5436260a1` |
| `results/mars/jezero__landing_mobility/convergence.json` | 482 | `16e531f569c11a0db4262bf9d13d806e8193dd3451605e10211c832ddda26eff` |
| `results/mars/jezero__landing_mobility/discovery.json` | 26706 | `d6b709b467503853bf55bb8eb42502aa644d0d5e359b53b4fa8dce46d6bb72e8` |
| `results/mars/jezero__landing_mobility/mc_counts.npz` | 6167968 | `3880cf84bd6a9862621dd0b6876debe86fce8629956471c201b8cdee8ad1d48d` |
| `results/mars/jezero__landing_mobility/mc_summary.parquet` | 3328385 | `51c2d0a111ae5e50d4343af04917740d3881c3c2846c571fb565f5607768603e` |
| `results/mars/jezero__landing_mobility/ml.json` | 1537 | `b89eaa0e86fe09c9d9d1f99c2d492284d4f7aa986a2c516c071351585e7ec952` |
| `results/mars/jezero__landing_mobility/summary.json` | 3021 | `491c4fc809086b145ec8d8c6896d4e51140e8e888418a5bcfa30059df5d0b453` |
| `results/mars/jezero__power_night/alt_weight_checks.json` | 415 | `8ba2fb083acdf8d1edc1c603fbf2acb22e967d3535efdfc75ef36ab4d1c47a4c` |
| `results/mars/jezero__power_night/base_scores.parquet` | 10796150 | `395064ce801508ff15680da55d0716b0f5d3dede935bc4fdfa2c40fc73cf3695` |
| `results/mars/jezero__power_night/convergence.json` | 484 | `c2ea125c962d0f9624b6363d64631ad9f558e28bf12e5bef28e7e41cff1d06c5` |
| `results/mars/jezero__power_night/discovery.json` | 26787 | `10a19a55a8b5681146d41600e28475156f52ac0cf541311fc8692839843a08e8` |
| `results/mars/jezero__power_night/mc_counts.npz` | 5985302 | `cea2aec4c7537276c4bfc39b60816cbfddbce96a630d346920ba0a697e949866` |
| `results/mars/jezero__power_night/mc_summary.parquet` | 3562295 | `4bfdbf1e57bfb5a1a28f9131615eb422ca2f9313206e1eb579ef39e43c8fca1c` |
| `results/mars/jezero__power_night/ml.json` | 1491 | `1adbd0db16945fae14f18624ea66620e745623292f515830a56a9ca7792e53bf` |
| `results/mars/jezero__power_night/summary.json` | 2997 | `46539a41c58cc3001c4c7c67396420e17de2b9bdcde4400a19ddbb51f9f237ef` |
| `results/mars/run_meta.json` | 2569 | `931c2f3754b5379c11be60e84b630c6427bfbccd0fe49c7ccf0be5a54660d4ef` |
| `results/mars/validation.json` | 9602 | `7df4fe948dda1ae84c488f537e97d26b6f9c582be43be19cfbf508ee286e9a68` |
| `results/moon/.done/discover__connecting_ridge_c1__base.json` | 286 | `4c3e4ed862530f7d43ad6227c9a7baf178d4b45d8d59f4b96e53760e0762539b` |
| `results/moon/.done/discover__connecting_ridge_c1__landing_mobility.json` | 299 | `8dd42bf35ac845f0b50e70caf193f1365e341e10a05bb5d50da3965bac559c06` |
| `results/moon/.done/discover__connecting_ridge_c1__power_night.json` | 294 | `2d20ec4b3dfbbcb3a07989adcc705013bc5baa331c0c9e1f141d8cd62aef2b1f` |
| `results/moon/.done/discover__shackleton_rim__base.json` | 282 | `13b8eb5b32c4f984bfbbc20feb4fc960e971b18f0cb637ca1ee39e86cede27d8` |
| `results/moon/.done/discover__shackleton_rim__landing_mobility.json` | 294 | `01217cab86915a2ee04db3ee664df264c791ae02fa242c9b3fc24045405a5541` |
| `results/moon/.done/discover__shackleton_rim__power_night.json` | 290 | `7b67f648d8eb196c7b5ce13370bbb50e45812458db65c6ca312b7cc03eae4c4c` |
| `results/moon/.done/gates__base.json` | 263 | `276203b1dd98f0ae8e91bf2e68cc769998a48233c31083ef6ddb2b9c79a81527` |
| `results/moon/.done/gates__landing_mobility.json` | 275 | `d1d96aa662af1b99544dcc860d4e45a0fff0bc4f9a73c2d04d576e0aacbfdde5` |
| `results/moon/.done/gates__power_night.json` | 270 | `fd278486761de02d0f2ee005e394ca225f70244b5ca1dbe4f994bbb36894b99c` |
| `results/moon/.done/ml__connecting_ridge_c1__base.json` | 279 | `9de61b100a42371fa5958425ab0cb994f489874ba931377a54cddfef7e6f2677` |
| `results/moon/.done/ml__connecting_ridge_c1__landing_mobility.json` | 292 | `d5ddaba7cd942239fbe9fd0979af040f73e5a61a1988f93cde0923e02886ce7a` |
| `results/moon/.done/ml__connecting_ridge_c1__power_night.json` | 287 | `d1a62090635c514897aeded5f0d4c5e70f6635d43916ee847f2eb538720c8a4e` |
| `results/moon/.done/ml__shackleton_rim__base.json` | 275 | `907bccd3f4a0649fd0744fda8643052782117e1c1aa3db0e8701c29230ffd087` |
| `results/moon/.done/ml__shackleton_rim__landing_mobility.json` | 286 | `aba9a7a002fa3d6930cedcfb624f2929d2fad9ab6ce1d080d68bc7602cfbdd8c` |
| `results/moon/.done/ml__shackleton_rim__power_night.json` | 282 | `ca4b7f20f49025a36aa5c42a99a1ff269f1ab93a9c6dd85e635457a7c597d59e` |
| `results/moon/.done/score__connecting_ridge_c1__base.json` | 311 | `e71bef8ef12ff06d01c2da2222119b800123c1835755c71ebdfec13752b10e98` |
| `results/moon/.done/score__connecting_ridge_c1__landing_mobility.json` | 323 | `1b134323d5f6aa7b9c52f071c5c5c72f18863fb8b54763c3449581183a26520b` |
| `results/moon/.done/score__connecting_ridge_c1__power_night.json` | 318 | `c8036330f296354e32962234fdfe1959c31cf00d8b672887c1cf794a4fa457ea` |
| `results/moon/.done/score__shackleton_rim__base.json` | 306 | `de450d6744dba5f15ab4df121b652ebf97f4c5d8c8c43b0a5ffe853e67259f65` |
| `results/moon/.done/score__shackleton_rim__landing_mobility.json` | 318 | `ca3c7616706cce29cd9fda458ae33287a804b6ef5e59812734c2342843951970` |
| `results/moon/.done/score__shackleton_rim__power_night.json` | 313 | `442e010fcffd8559470a95fb2eb4883a088db676fca427d4c36d0669d38209c9` |
| `results/moon/.done/simulate__connecting_ridge_c1__base.json` | 314 | `b3bddc35999b81d80bf472d4c016203fb4eddde24bd3e399157961019e615b12` |
| `results/moon/.done/simulate__connecting_ridge_c1__landing_mobility.json` | 326 | `72427acd357eafa6aceb41626d7ecbec6e2dd4108e05d3d9685b6967679d9208` |
| `results/moon/.done/simulate__connecting_ridge_c1__power_night.json` | 321 | `40a062e594c78c4ae80cc3cadd1a37fbbe2771fa3d9ff1a0269724e220b46e15` |
| `results/moon/.done/simulate__shackleton_rim__base.json` | 309 | `efc82ab27fe4f8e37cafce3aafa82f1aa10be636953125ad7ef9b130dcc19c81` |
| `results/moon/.done/simulate__shackleton_rim__landing_mobility.json` | 321 | `c372497672184b0cb8ecd46483a925541fe6f508217c8e429d64cb621f50e8a7` |
| `results/moon/.done/simulate__shackleton_rim__power_night.json` | 315 | `d1c79424f80759d11984b768a884819f059a5e0cf8b3e45590060b748764a156` |
| `results/moon/.done/validate__body.json` | 264 | `5216b94c1269d67e59dae3907a132eeedce84498674a7ddae54f7c861ab6c188` |
| `results/moon/connecting_ridge_c1__base/alt_weight_checks.json` | 691 | `f9f11f1814c6d0a715e3b2b97f7b494b83a16ce7fe0f791169bb37478ae78bee` |
| `results/moon/connecting_ridge_c1__base/base_scores.parquet` | 11335939 | `12cc95c3a63fbdd5143213d11e2b84628682c94ea5a242330e5972292dab9045` |
| `results/moon/connecting_ridge_c1__base/convergence.json` | 483 | `3d4965cd1f8dcdf10d89265ec802354e2737b9bff37d5a67dc3ac36ccaa40d11` |
| `results/moon/connecting_ridge_c1__base/discovery.json` | 27219 | `7f3761add0ad1ca9671e839b5cf118f81cbf83d6eab6930bbb4179d1ed4d5b0e` |
| `results/moon/connecting_ridge_c1__base/mc_counts.npz` | 7672851 | `dfddb5115b77e032d1725abfb454d99b090744ba958f8d7d79e51aa168f83b2f` |
| `results/moon/connecting_ridge_c1__base/mc_summary.parquet` | 2848670 | `888db9645b9135712c737c9d1083c0632ffdfc466c7dcda452046a48f3c103d9` |
| `results/moon/connecting_ridge_c1__base/ml.json` | 609 | `07cb06c563b070ecab194dd1bc323b9fc80929077b43e9b533a1458db5e06ae6` |
| `results/moon/connecting_ridge_c1__base/summary.json` | 2773 | `1907d69d259ffcf3b6fddc0df863aba4ceebfb101bcd38ba3274263a1cf691af` |
| `results/moon/connecting_ridge_c1__landing_mobility/alt_weight_checks.json` | 690 | `00ea926053e36dbe1f0f1135df3be12efe180892ee6f3d5f3cd1b9cc42df0bed` |
| `results/moon/connecting_ridge_c1__landing_mobility/base_scores.parquet` | 10103295 | `aa38293fd4c59501038f6e82dad4709b3ac4edce30f60704dd406e8f3fd6b9c9` |
| `results/moon/connecting_ridge_c1__landing_mobility/convergence.json` | 482 | `be13b6736611b9bbfd28e90a05df9da322daf65dfe0942d0e906940dcf6cfc6d` |
| `results/moon/connecting_ridge_c1__landing_mobility/discovery.json` | 27164 | `b1bd5915771e7e5841e82cefeb81213229ede30e1dabc8385b73373483296a1f` |
| `results/moon/connecting_ridge_c1__landing_mobility/mc_counts.npz` | 6773591 | `ca03b9bc8d0e2554cfaa81bb8acbf88240710dd7c3ba2202bbd4fef01c6db38c` |
| `results/moon/connecting_ridge_c1__landing_mobility/mc_summary.parquet` | 2757226 | `47305e456f4f73ba1fad816c2b1dac9c57b4eeaeadca42604b744bfb761396c1` |
| `results/moon/connecting_ridge_c1__landing_mobility/ml.json` | 589 | `49461e23444696927dae363557a73b4318e5f149eafb7f7607d0434401fb9c39` |
| `results/moon/connecting_ridge_c1__landing_mobility/summary.json` | 2806 | `21086f9d8227dbb9b29e6f40f4b07ef805a06c9c012afdb0d5dbda86a79b1ffe` |
| `results/moon/connecting_ridge_c1__power_night/alt_weight_checks.json` | 689 | `89d2514f710ac690aa3eead58525c6e3bbb1ac16d58a1fb912a8c5cfc90c5b51` |
| `results/moon/connecting_ridge_c1__power_night/base_scores.parquet` | 11335683 | `2a9d57fdf2c8eb5932e8e94658b973bf6660a74d4557fe92a93374fa009f89a9` |
| `results/moon/connecting_ridge_c1__power_night/convergence.json` | 482 | `60814c614afb953cf925f66f640432dd274da021fb40591aa028f39190deeb4c` |
| `results/moon/connecting_ridge_c1__power_night/discovery.json` | 27226 | `2f9e511eabcee987004311f6c76c991f9ff3bc18330f68f892c5870aadf4e9a2` |
| `results/moon/connecting_ridge_c1__power_night/mc_counts.npz` | 7652229 | `91f952796ccc42f08860b6a7cf4ea47f14edbd5f9e0a5b1f0856e76c45ab8d2a` |
| `results/moon/connecting_ridge_c1__power_night/mc_summary.parquet` | 2843876 | `e5cb363a63e5da1120a23c67a6c8af5b6d4c966b0c9675bd72de618614809879` |
| `results/moon/connecting_ridge_c1__power_night/ml.json` | 609 | `07cb06c563b070ecab194dd1bc323b9fc80929077b43e9b533a1458db5e06ae6` |
| `results/moon/connecting_ridge_c1__power_night/summary.json` | 2774 | `693a3436fb30f234f453fd3a4425353eea7b46bba5cbd15a63e0acd9609ef83a` |
| `results/moon/export/MANIFEST.json` | 2325 | `518b7e0b116b024509a78de2b71f49f1363c9106f4d80f3ca3ce35556640e127` |
| `results/moon/export/candidates__connecting_ridge_c1__base.json` | 191518 | `27d3d721b64cd8fcd51cf04f434b35765e57266343f7b82ffadc5bbf36f133ee` |
| `results/moon/export/candidates__connecting_ridge_c1__landing_mobility.json` | 191279 | `8546aac848cd54bf096aa62aa0a2b3ed68227307c8983ada137e646f3cb6d8e8` |
| `results/moon/export/candidates__connecting_ridge_c1__power_night.json` | 191441 | `aaf33401d9f4697d0d9d35a6e4c1d500a2c98ea77f76435c1343bddea71f3139` |
| `results/moon/export/candidates__shackleton_rim__base.json` | 191022 | `d161e72542407d3d26516af3f12742c04c9d19c335ad4931937a98e68f61cb09` |
| `results/moon/export/candidates__shackleton_rim__landing_mobility.json` | 188675 | `7993e500e2a3ac39163eb827b0e13563bc74b690a567d67ceef1b3e992b1acd0` |
| `results/moon/export/candidates__shackleton_rim__power_night.json` | 191026 | `88b8ff3f70c6751878e8aa1480be800eda0d7a82d9b5b01998fc570cc3bda42a` |
| `results/moon/export/convergence__connecting_ridge_c1__base.json` | 483 | `3d4965cd1f8dcdf10d89265ec802354e2737b9bff37d5a67dc3ac36ccaa40d11` |
| `results/moon/export/convergence__connecting_ridge_c1__landing_mobility.json` | 482 | `be13b6736611b9bbfd28e90a05df9da322daf65dfe0942d0e906940dcf6cfc6d` |
| `results/moon/export/convergence__connecting_ridge_c1__power_night.json` | 482 | `60814c614afb953cf925f66f640432dd274da021fb40591aa028f39190deeb4c` |
| `results/moon/export/convergence__shackleton_rim__base.json` | 482 | `3cfe6dda514ad9ec5e02f35cfa65494cbcd7b4a4b28cbd64e1a5265f5be1f81f` |
| `results/moon/export/convergence__shackleton_rim__landing_mobility.json` | 483 | `149acc22d813bb7fac022e7d1400d65738b3f719ed98d45248882646b0989172` |
| `results/moon/export/convergence__shackleton_rim__power_night.json` | 481 | `1614c00b195319ada23e17479ce58bc9e445d3b6e25c8d7e257a5860891edcb5` |
| `results/moon/export/fidelity.json` | 10592 | `e32862d7f3fbe73fe76b499def50a54fffbb7e760905ac0a2acba44febc6ef9d` |
| `results/moon/export/index.json` | 2834 | `a7d4c0723af3d01188431fb186a3cbc3d033278b63a6ab88e96fd6ff5fb006be` |
| `results/moon/export/validation.json` | 10856 | `68c9ae4d447782a3d834383a9873b8f75e9407cdc7aede5f54c42493eef4870b` |
| `results/moon/gates__base.json` | 205 | `180f5b98ef1fabd2c2453612027a50237606414a7fb83ba11a172e88c5309cec` |
| `results/moon/gates__base.parquet` | 17239396 | `059fa835ff02bdb7cf1c687b86898748305558de649c9e888cd0ce6dd06e4c6c` |
| `results/moon/gates__landing_mobility.json` | 241 | `4498484d7c9d4167b469b25e294d758f82d4aaadf315c5879f7f6ee4cdcceba1` |
| `results/moon/gates__landing_mobility.parquet` | 17296413 | `56a139fdfc7a0ab52c73fd9936777dbc3bbf906b9d08390a2b298ed3606e68a2` |
| `results/moon/gates__power_night.json` | 212 | `3053e4a30fbf60176f14517fc56883de42ada90f7c0b1594897c893eed3cd4d3` |
| `results/moon/gates__power_night.parquet` | 17239396 | `059fa835ff02bdb7cf1c687b86898748305558de649c9e888cd0ce6dd06e4c6c` |
| `results/moon/run_meta.json` | 3321 | `33d8771b37cd1b3c369ee9df45f1db627430ebe82d5d6a4c53016b314a2fc59d` |
| `results/moon/shackleton_rim__base/alt_weight_checks.json` | 691 | `5c40526cf72f5a65de27a0be21f07c345564e6611a706fbeb28e115c485b0039` |
| `results/moon/shackleton_rim__base/base_scores.parquet` | 11307606 | `80a272f80d558fe70a7159692f6e11fc2f3b502b6f9f759df1b7d2fd6e47acb5` |
| `results/moon/shackleton_rim__base/convergence.json` | 482 | `3cfe6dda514ad9ec5e02f35cfa65494cbcd7b4a4b28cbd64e1a5265f5be1f81f` |
| `results/moon/shackleton_rim__base/discovery.json` | 27156 | `8048f187bd35180e2f49123fd0e76549d081584888e56f5baffa326218e3b733` |
| `results/moon/shackleton_rim__base/mc_counts.npz` | 6994197 | `125cd626c49602f13163b744d976fb1c3fade90da27daa33d654cb1de463e20d` |
| `results/moon/shackleton_rim__base/mc_summary.parquet` | 2843902 | `1090b2b5a7d305a95093ecf72f69f689de5326fb43528c6f0efc5a0a1f28cf70` |
| `results/moon/shackleton_rim__base/ml.json` | 609 | `d54eb02507ca2a126be782060f143a6baf70f1053541802bac5eae8f33b5d1b1` |
| `results/moon/shackleton_rim__base/summary.json` | 2779 | `fac186fa1f4ad3c4adbb1742a7797fbe3e556e6050ed97fb5237d93ad5597f4b` |
| `results/moon/shackleton_rim__landing_mobility/alt_weight_checks.json` | 690 | `a7a60ceef6fcec2a663f8b55a21007c2a9c8d4d07a55c6c09fd31d1c3c45217b` |
| `results/moon/shackleton_rim__landing_mobility/base_scores.parquet` | 10090530 | `0edd175b0769b435f54644c871dad959078ed3c87eef414dd070de4fe8d39ef9` |
| `results/moon/shackleton_rim__landing_mobility/convergence.json` | 483 | `149acc22d813bb7fac022e7d1400d65738b3f719ed98d45248882646b0989172` |
| `results/moon/shackleton_rim__landing_mobility/discovery.json` | 27076 | `4a3ca3983046b59cab7c12542e50605357803162aceef8d42ca1c648172e8ac0` |
| `results/moon/shackleton_rim__landing_mobility/mc_counts.npz` | 6351012 | `0ef7619edd2d1ab900e6396c804369bdee88adec964a5db082ddf858712d0c0e` |
| `results/moon/shackleton_rim__landing_mobility/mc_summary.parquet` | 2696753 | `edb22eb3a5ca73f23198860bc27aa1e4f37dd9a6e6744a766e15ed736c41c35a` |
| `results/moon/shackleton_rim__landing_mobility/ml.json` | 593 | `0d0b48734c00a74d2546c739e95ef13537b031b8b60bba13bfc582f59c013974` |
| `results/moon/shackleton_rim__landing_mobility/summary.json` | 2812 | `dbf199730b9e142b8e7b6661b3bf3d5336e9e3de84a22bc594088635667c5fed` |
| `results/moon/shackleton_rim__power_night/alt_weight_checks.json` | 690 | `d3e7d65f78b175aa4963a7f57ce0c4867046fa5940a3a61199106bfa30336b3e` |
| `results/moon/shackleton_rim__power_night/base_scores.parquet` | 11307726 | `d2793891762ed96765c048dab2c1d8c301719272917bc372ea047d4e83387bcf` |
| `results/moon/shackleton_rim__power_night/convergence.json` | 481 | `1614c00b195319ada23e17479ce58bc9e445d3b6e25c8d7e257a5860891edcb5` |
| `results/moon/shackleton_rim__power_night/discovery.json` | 27153 | `fbe4fd454fb09b11c4bf50030f169ad7e5da98046b3fee06df4e7a3f2b68a1f7` |
| `results/moon/shackleton_rim__power_night/mc_counts.npz` | 6929273 | `639094fe0592f12d33204abf148ea6baf9a4e5aea48f91ea948bf14b601c6f4c` |
| `results/moon/shackleton_rim__power_night/mc_summary.parquet` | 2836092 | `652385d241ffc97e9f4eab8e04b2c07def764b5eca2a67d006a5cc2f10152234` |
| `results/moon/shackleton_rim__power_night/ml.json` | 609 | `0318605e7690916963845e72ea60ad3bffdc088bc81ab933faf9705bbf59661f` |
| `results/moon/shackleton_rim__power_night/summary.json` | 2779 | `bdfe6ae88fe7b104c243d675b3f9bd7c842daadf196ced046d89f892aecd4576` |
| `results/moon/validation.json` | 10856 | `68c9ae4d447782a3d834383a9873b8f75e9407cdc7aede5f54c42493eef4870b` |
| `results/moon_lat20-40/.done/discover__connecting_ridge_c1__base.json` | 297 | `67a9d28deac6e33b101ac49b18233a153d7b9a59190739cfc4013f46ab667084` |
| `results/moon_lat20-40/.done/discover__connecting_ridge_c1__landing_mobility.json` | 308 | `211a951f5456dab1c8f279a0f7aa6757c9fbc9c6bf3c845259f56415865fe293` |
| `results/moon_lat20-40/.done/discover__connecting_ridge_c1__power_night.json` | 303 | `3984f9385632e7e377b4304f1c6728c024e1b691a9f4d731785d2117a55b00e0` |
| `results/moon_lat20-40/.done/discover__shackleton_rim__base.json` | 291 | `2ae216a80212493de677758f696f65164fcf3d2335f2c4b2ee2d47c6d7e2834d` |
| `results/moon_lat20-40/.done/discover__shackleton_rim__landing_mobility.json` | 304 | `fb7e17161e3c2e44db622eae683193dbf43b77dc43af75cd57f0c9cae9427a00` |
| `results/moon_lat20-40/.done/discover__shackleton_rim__power_night.json` | 298 | `8ec2f61f58957497664c9e9f6ecb6009e097ef5061f099fd648840d17114f5e8` |
| `results/moon_lat20-40/.done/gates__base.json` | 272 | `f38fd993682eda3a38272ea31fb7379b31a85420ea51c3307be4508eddcc80b4` |
| `results/moon_lat20-40/.done/gates__landing_mobility.json` | 284 | `d6962ea61779fbe3ad16da7a643ac3e22d6ac103ece5f5e90cd9b17f3385aa0c` |
| `results/moon_lat20-40/.done/gates__power_night.json` | 280 | `616dba1cd23354b193f0c9d73b1418cb6be348856c0f1da0b1657a0a9db77885` |
| `results/moon_lat20-40/.done/ml__connecting_ridge_c1__base.json` | 289 | `8351a4d5b7ea8f7fc0c679f403d76a1649073451d76eca9de16132995f3c97e4` |
| `results/moon_lat20-40/.done/ml__connecting_ridge_c1__landing_mobility.json` | 302 | `ce9615d5b3620cd960e2ed331caea251f8355befa0d7e6cffbd49803ccb31228` |
| `results/moon_lat20-40/.done/ml__connecting_ridge_c1__power_night.json` | 296 | `a81ff186b3102bdd89cb50a01142671845d9c7589b1755007edbd613ef4fe6e3` |
| `results/moon_lat20-40/.done/ml__shackleton_rim__base.json` | 284 | `004fa038d6aa69ae9fb4b03d239870a0c7aae47218d46ba41969d55b549f5732` |
| `results/moon_lat20-40/.done/ml__shackleton_rim__landing_mobility.json` | 296 | `3691035d7ab0a0dbd2152810be1f2d2e0ff2914d7e25c22cf20ce6d5d4efa7a2` |
| `results/moon_lat20-40/.done/ml__shackleton_rim__power_night.json` | 291 | `9817e3d3d123e7e9b825d68e2edc3fa14f882fe78b775d77e782d55508f995bd` |
| `results/moon_lat20-40/.done/score__connecting_ridge_c1__base.json` | 320 | `eabb47f25acd8e8f5627ddb73c3ce0ccd6861c2de029a88180dbad54f30e54d8` |
| `results/moon_lat20-40/.done/score__connecting_ridge_c1__landing_mobility.json` | 332 | `78e8ee666e83d3644279f79298635fbdf72520f58e3951bb9583f00abd547f1f` |
| `results/moon_lat20-40/.done/score__connecting_ridge_c1__power_night.json` | 327 | `850cc424b5d4b5739727230b83660fffe0167006edc8466cd11b73808640fffc` |
| `results/moon_lat20-40/.done/score__shackleton_rim__base.json` | 315 | `76265505a286092085969cd971a514e7267b80fba9732a53c4ac36e05f3cf40d` |
| `results/moon_lat20-40/.done/score__shackleton_rim__landing_mobility.json` | 327 | `0a015c9f45d1dca5438721f15c02bd85ae2a5e87ce051f2dda92eb1bbd64b21d` |
| `results/moon_lat20-40/.done/score__shackleton_rim__power_night.json` | 322 | `571230690e3236e23d1aca269b219f3289dcebe1230bf4e5c6eebfad9d3ef311` |
| `results/moon_lat20-40/.done/simulate__connecting_ridge_c1__base.json` | 322 | `1939195cd5c805b3cdb129e38d624612d3ef0fcea70d73007ea7866f16332e42` |
| `results/moon_lat20-40/.done/simulate__connecting_ridge_c1__landing_mobility.json` | 334 | `dda1dcad0ae3e00fb251bf1117726f7a5729c297804e1c494b8e1bd22ed3cb3e` |
| `results/moon_lat20-40/.done/simulate__connecting_ridge_c1__power_night.json` | 329 | `eba4e7d24e445722730bc602b4663bd34bc3289124ee4411e4626885475a6782` |
| `results/moon_lat20-40/.done/simulate__shackleton_rim__base.json` | 317 | `56d292e8781dbc0f655acacf55cb70784514a9514c80fbdfd23446d7a3120e61` |
| `results/moon_lat20-40/.done/simulate__shackleton_rim__landing_mobility.json` | 329 | `0ff629e52c40d34535e83df5992141e651cf7430940fdf0a615002c15d97632f` |
| `results/moon_lat20-40/.done/simulate__shackleton_rim__power_night.json` | 324 | `4877e944c248c92faf0b390838e25381e2d655762969beb693fba16a03314a63` |
| `results/moon_lat20-40/.done/validate__body.json` | 275 | `ea965f50e2e5c831fd330e96e75430d6827236ab5e56ae6bb25f0c992ca163bf` |
| `results/moon_lat20-40/compare_with_full.json` | 14821 | `1fca0294c487942a11c07404280ed1608a62174dfdb6da5171a34b45f924fd63` |
| `results/moon_lat20-40/connecting_ridge_c1__base/alt_weight_checks.json` | 691 | `acdec7716a6e33bd1fd4af077d75a5ee2cc91d21986774bea387b6f20b780d63` |
| `results/moon_lat20-40/connecting_ridge_c1__base/base_scores.parquet` | 5242713 | `89fee554a021a46f8df23251a5ad17f22a970fabef9a0a17f4b9f8463f541a50` |
| `results/moon_lat20-40/connecting_ridge_c1__base/convergence.json` | 483 | `0082aa82352937fa672ca3bcae634aeda0fbd8c96f47c23d302e37413631e451` |
| `results/moon_lat20-40/connecting_ridge_c1__base/discovery.json` | 27259 | `5971bd7efea33dd62c9e22cbfbd7221dbbd4660f01a98de8898b25565aa57b18` |
| `results/moon_lat20-40/connecting_ridge_c1__base/mc_counts.npz` | 3378403 | `9d28175e40e6149eb6086eaa910274e3b2cd54cd803cf38f8522d1ffa6837a43` |
| `results/moon_lat20-40/connecting_ridge_c1__base/mc_summary.parquet` | 1268189 | `3449b0936f8489f529cb4b5a979bec942a33b7794dbcefd6f844f6b8c5af3d29` |
| `results/moon_lat20-40/connecting_ridge_c1__base/ml.json` | 572 | `20f5298d6f43f3fcb718511bc30c2f25e24faba125c36fac7b5e71add17ab0f2` |
| `results/moon_lat20-40/connecting_ridge_c1__base/summary.json` | 2772 | `153efca69ff62429d5a06e1866cf5ef42a38e7db3b88691990c93a75ca43afed` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/alt_weight_checks.json` | 689 | `36f6b28273006b0cef4dae5a83ea88c6e9e2ef2e81d0f70de3e4984d27054d88` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/base_scores.parquet` | 4907435 | `0e25907fca03ea6b7fef82d60993015f10bcb1c00c0ca438561ab76c9208962a` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/convergence.json` | 483 | `a22de02757d7b6b9cdcae9d416eb2764436aa184f5e2a0600270100d84eda577` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/discovery.json` | 27249 | `2d315d45097d04d4e7f608c6398aef845c85358cacc3b47b7df2370b89e95c54` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/mc_counts.npz` | 3041495 | `a4b774b372208f46f140e1cfe647000630c20bda0ec88a04104c5c8b61a01061` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/mc_summary.parquet` | 1282196 | `5136e7bac2d29590457de24dbdd9e018565188cbc8e56baf4968ee864a4de354` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/ml.json` | 557 | `dc7e616bec20fd1cc21cb9b64727c7c6746e5910a5af38f352b683c1887cf30e` |
| `results/moon_lat20-40/connecting_ridge_c1__landing_mobility/summary.json` | 2798 | `5f7ab59b2505421842da81f8caf9e693dfd8ec0b53d3f49f71f4fc4281c9bedc` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/alt_weight_checks.json` | 690 | `d1b359b16f222a3888272772a51f61401919046f03f66db6d47a6d8c7ca6bf03` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/base_scores.parquet` | 5242665 | `5b615fc088f6289f979f497cd9ce4e8e1d7eef082157a8b81b91470934b6e4b5` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/convergence.json` | 483 | `9cdcc40da18f0eade9ac5a21850ba3ff1391e447f0c706d924009337cc4ba0ce` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/discovery.json` | 27259 | `b02e07125a6a8c38c36a9fdbfcb4419ead106cac1de31d73a62dad7a19f344a2` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/mc_counts.npz` | 3366382 | `fd15d86c2b3e02cce221cbcb5992c2a87ee62cb4ecd6e200ad1a0393ecd4806a` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/mc_summary.parquet` | 1266451 | `66e7b809b675c6be97e1c4ef4bba616ea581ce6344ac7f945b25b4b3e7eedc3f` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/ml.json` | 572 | `20f5298d6f43f3fcb718511bc30c2f25e24faba125c36fac7b5e71add17ab0f2` |
| `results/moon_lat20-40/connecting_ridge_c1__power_night/summary.json` | 2772 | `5484cf42889feb44370ac506839a0185f4f3af46e05464b20b5efe4acf181dcc` |
| `results/moon_lat20-40/export/MANIFEST.json` | 2325 | `a0e946513d92700cb93c4a7206248422f97f724661d14b647ccbddcab9a05cf3` |
| `results/moon_lat20-40/export/candidates__connecting_ridge_c1__base.json` | 189617 | `133e01026380a44dba261609ec0582aaa6a27fc6fdb28c594886525b91102a54` |
| `results/moon_lat20-40/export/candidates__connecting_ridge_c1__landing_mobility.json` | 189000 | `fd62b2431f00c506d9a1de57daafcc9416dca975e323f1e9b41993b3311a82a8` |
| `results/moon_lat20-40/export/candidates__connecting_ridge_c1__power_night.json` | 189619 | `297b28b65a2b665ec9dc3c589a58fb593158292b76ac0f35e25e06f14e277c2b` |
| `results/moon_lat20-40/export/candidates__shackleton_rim__base.json` | 188372 | `d7416082f83a1bca0e6e38aa2f122bf124d67d26ec3d315d2b72afd8161d0f3e` |
| `results/moon_lat20-40/export/candidates__shackleton_rim__landing_mobility.json` | 186758 | `a1c5a30f397701587728394ed6c6ea59ea3c274f2691c43a87c089b700b81205` |
| `results/moon_lat20-40/export/candidates__shackleton_rim__power_night.json` | 188434 | `15210dd1b57afed96c13b0ecfd679df11c5f406bdba4e2ebecfca7322aa2d418` |
| `results/moon_lat20-40/export/convergence__connecting_ridge_c1__base.json` | 483 | `0082aa82352937fa672ca3bcae634aeda0fbd8c96f47c23d302e37413631e451` |
| `results/moon_lat20-40/export/convergence__connecting_ridge_c1__landing_mobility.json` | 483 | `a22de02757d7b6b9cdcae9d416eb2764436aa184f5e2a0600270100d84eda577` |
| `results/moon_lat20-40/export/convergence__connecting_ridge_c1__power_night.json` | 483 | `9cdcc40da18f0eade9ac5a21850ba3ff1391e447f0c706d924009337cc4ba0ce` |
| `results/moon_lat20-40/export/convergence__shackleton_rim__base.json` | 483 | `71cfbe9347766682eafb7aa509b0f288b7209e47f1215b526db32c5237c5d1cf` |
| `results/moon_lat20-40/export/convergence__shackleton_rim__landing_mobility.json` | 481 | `d975ece35267b13497635c53f4af4e729e96d1350c59fcc684bba2e7b705d066` |
| `results/moon_lat20-40/export/convergence__shackleton_rim__power_night.json` | 483 | `e1c020174bab35b91cdf4f06d8f3fb43cc98ff6e19e4f96b9c60e392149a53dd` |
| `results/moon_lat20-40/export/fidelity.json` | 10592 | `e32862d7f3fbe73fe76b499def50a54fffbb7e760905ac0a2acba44febc6ef9d` |
| `results/moon_lat20-40/export/index.json` | 3026 | `11c3f409f6e3fabad4b1211c7658bf2f7159d58943ecc6f6c7720394f7c8e4fb` |
| `results/moon_lat20-40/export/validation.json` | 10097 | `af968bb70314724d30d2a9a523a98c4b0f2380dbf98755f9466431191cf908eb` |
| `results/moon_lat20-40/gates__base.json` | 200 | `c2d6f2d6eb3a81fa9df8dae14cfc420e31f9a0f471409ff1e437d398ad6d9ee5` |
| `results/moon_lat20-40/gates__base.parquet` | 5525992 | `6d8ae462add220a52517d8083d71b87cf09858cab4e8636de2a348369f17b139` |
| `results/moon_lat20-40/gates__landing_mobility.json` | 235 | `25cda4dacc0b98da305cc401dc16688c50672a6f7d9a40092956ebeca29309cc` |
| `results/moon_lat20-40/gates__landing_mobility.parquet` | 5548960 | `76e4c4681a102d5d59be08b05c60e7c06f2f27b1db07a0009c3c68d82b1efd81` |
| `results/moon_lat20-40/gates__power_night.json` | 207 | `46d42141103bd7d7cc89bcd0cd8b5c1f7a8be3881a8ee03e9c96983d3f608368` |
| `results/moon_lat20-40/gates__power_night.parquet` | 5525992 | `6d8ae462add220a52517d8083d71b87cf09858cab4e8636de2a348369f17b139` |
| `results/moon_lat20-40/run_meta.json` | 3527 | `c7eed9d97f816c962471bf9d2785aebb85436c2a15217b4987b03adc02bb95b4` |
| `results/moon_lat20-40/shackleton_rim__base/alt_weight_checks.json` | 691 | `41feadc0f76aea2912c181306e3a9f6db05186526ecfc6955cba5f39593fd9c8` |
| `results/moon_lat20-40/shackleton_rim__base/base_scores.parquet` | 5234861 | `ffef9363ddc45b8c5b73fbd2eb6b666cf9233403d9128475960cd76251198b94` |
| `results/moon_lat20-40/shackleton_rim__base/convergence.json` | 483 | `71cfbe9347766682eafb7aa509b0f288b7209e47f1215b526db32c5237c5d1cf` |
| `results/moon_lat20-40/shackleton_rim__base/discovery.json` | 27272 | `637e5dbb78a045289db9d1a2e041d8e4c2ca90856322b12cab61cb88dcd1522a` |
| `results/moon_lat20-40/shackleton_rim__base/mc_counts.npz` | 3114611 | `38da5735173036361d43be5e5f6646793f3c94ed56dc2c55d3e82b0812ba0222` |
| `results/moon_lat20-40/shackleton_rim__base/mc_summary.parquet` | 1246081 | `243b76079678188bae48353b2e22d330a9f8068450870dce5c72d500c7740a13` |
| `results/moon_lat20-40/shackleton_rim__base/ml.json` | 572 | `047b35f2c6ef0a52885bd05ff811ab55eca7f530323a4cd448184df491e147a0` |
| `results/moon_lat20-40/shackleton_rim__base/summary.json` | 2774 | `d38c8918cf4f1af971a8792df0cdcd553093465b6b491278f7f3d6d3144d35f3` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/alt_weight_checks.json` | 690 | `79d4d584f4909e62ebcd6d9cf0a396fda6c738129fb2395cc71e840b9f1e9b40` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/base_scores.parquet` | 4895880 | `7c926e64c3c02d73a96247d060c02d021cf0b796792642bbd024709acc708bdc` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/convergence.json` | 481 | `d975ece35267b13497635c53f4af4e729e96d1350c59fcc684bba2e7b705d066` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/discovery.json` | 27152 | `9886f9dfe9ebeb8fdacfe8ad01446881cebac805edce674c60d0a1c14ec5c423` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/mc_counts.npz` | 2861083 | `46fa768f33565d12ae591905446408a73ef3d0e327c2aa91f8c4681137019f95` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/mc_summary.parquet` | 1219812 | `64c7326a64e2db67aa206bf421a73cefa380d3b41fce856f493373dd6ad081ff` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/ml.json` | 560 | `218d23105779e069608c42d4edc1bbf671fe790a46076d11deb29bed8f0acc9a` |
| `results/moon_lat20-40/shackleton_rim__landing_mobility/summary.json` | 2808 | `d944284da4b98b46a214af1b468709fa1a6b474d19475c37a0831fb1914e1c1f` |
| `results/moon_lat20-40/shackleton_rim__power_night/alt_weight_checks.json` | 691 | `654f4abf6aaf0efd063929109f0287e52ee921713b937856b5e6d9c3452b1015` |
| `results/moon_lat20-40/shackleton_rim__power_night/base_scores.parquet` | 5234601 | `27c395500b87a248b76f02392aeed0583529629e54c17429033e6a0d2b4728a2` |
| `results/moon_lat20-40/shackleton_rim__power_night/convergence.json` | 483 | `e1c020174bab35b91cdf4f06d8f3fb43cc98ff6e19e4f96b9c60e392149a53dd` |
| `results/moon_lat20-40/shackleton_rim__power_night/discovery.json` | 27273 | `67831b4d235bb4ca85657838866b7d8a1cf66999587592034816cdf16b3cb37d` |
| `results/moon_lat20-40/shackleton_rim__power_night/mc_counts.npz` | 3085815 | `7cd7a00cb3ca524ef42e6a62adfe0126eba3e33ab91b785d8352e717bc8fd932` |
| `results/moon_lat20-40/shackleton_rim__power_night/mc_summary.parquet` | 1242299 | `5bd906e990f71716a5d69af0f6a37c5e9f6d124fdfdc9810e075de0ae179e595` |
| `results/moon_lat20-40/shackleton_rim__power_night/ml.json` | 572 | `047b35f2c6ef0a52885bd05ff811ab55eca7f530323a4cd448184df491e147a0` |
| `results/moon_lat20-40/shackleton_rim__power_night/summary.json` | 2777 | `167c0a9dfa475467548bdcf7ea51d40abc30ad89edbd940ee01a600e34d3f6ed` |
| `results/moon_lat20-40/validation.json` | 10097 | `af968bb70314724d30d2a9a523a98c4b0f2380dbf98755f9466431191cf908eb` |
| `site_data/README_site_data.md` | 2338 | `65fcad906cd752453d4cca1924633efc5cd544b877f7edd0ef3be58ecb097da5` |
| `site_data/candidates_mars_jezero__base.csv` | 75160 | `833d0023aa965128913c0cd30617876eb411476c2049d70c915be3e719fc9e46` |
| `site_data/candidates_mars_jezero__base.geojson` | 237504 | `cdb12c7bfdbbf61febbe3112b95866866fe0bb05193a9c44fe5929a14c6e827f` |
| `site_data/candidates_mars_jezero__ice_resources.csv` | 75160 | `833d0023aa965128913c0cd30617876eb411476c2049d70c915be3e719fc9e46` |
| `site_data/candidates_mars_jezero__ice_resources.geojson` | 237504 | `cdb12c7bfdbbf61febbe3112b95866866fe0bb05193a9c44fe5929a14c6e827f` |
| `site_data/candidates_mars_jezero__landing_mobility.csv` | 75144 | `7a4e6a6b12cd4211c08c35c5c5300d1337e5a5e60199760ad0f86e469cf42842` |
| `site_data/candidates_mars_jezero__landing_mobility.geojson` | 237490 | `fdcc5d4bd62706a927592dfa950eec29b365a1c3b3e6e075db29bdf3ee3196ab` |
| `site_data/candidates_mars_jezero__power_night.csv` | 75101 | `ef436259e8c72e24662b02765d5878d9b904bf5fedfc544ac69df8cddb7ef098` |
| `site_data/candidates_mars_jezero__power_night.geojson` | 237445 | `d97b8f94de39b3e36766ccf1176df4aa806a8272945ad6a3e83a78ead09eac5a` |
| `site_data/candidates_moon_connecting_ridge_c1__base.csv` | 80688 | `de6c8b006e076f72124efd5062af9d51361be9c93bdd99d7d66d149a564e6274` |
| `site_data/candidates_moon_connecting_ridge_c1__base.geojson` | 243083 | `1242766241a350a6a71466619ff13cfe0aff8a8cb7c04f0d1075a47286b7cfa5` |
| `site_data/candidates_moon_connecting_ridge_c1__landing_mobility.csv` | 80612 | `b91d9dfe5c9e37976c3f12cf7ee6134ea0858c6e50587565604943f93639b372` |
| `site_data/candidates_moon_connecting_ridge_c1__landing_mobility.geojson` | 243000 | `53297ee84c84f584a6c978aa641dc9cd237bd0b73b974b8d9ce21b0af13a9e9b` |
| `site_data/candidates_moon_connecting_ridge_c1__power_night.csv` | 80604 | `be729c69fb7352ac0dc76f036d3f53f3ff363224a061ab8c0b816774600b13f7` |
| `site_data/candidates_moon_connecting_ridge_c1__power_night.geojson` | 242997 | `d4f79531ca914a8ee33500a8e4c8fa5e2f83d6e36a1bf64bac1fb1a78aeb06f0` |
| `site_data/candidates_moon_lat20-40_connecting_ridge_c1__base.csv` | 79276 | `4b5f02eb7a339e34ca1952920192163767d7aacfbfaf5f20ff4a249e297047d8` |
| `site_data/candidates_moon_lat20-40_connecting_ridge_c1__base.geojson` | 241676 | `d45c90936b494febbb2f7a5d89a7e822602f8da1094b76569ef13d7a1eba1e79` |
| `site_data/candidates_moon_lat20-40_connecting_ridge_c1__landing_mobility.csv` | 78670 | `6c674f24f5c61aed67d78e9d9181c22c161f5dffe9698a3d0db4d5ec1b13b549` |
| `site_data/candidates_moon_lat20-40_connecting_ridge_c1__landing_mobility.geojson` | 241036 | `13775879dbd4807f4841f26edfae60126306663689efbaa66920b520f8abf07c` |
| `site_data/candidates_moon_lat20-40_connecting_ridge_c1__power_night.csv` | 79281 | `7e8d9dc297156308a328c39ce8719b1fdc1041fcfe145cd6b03886177f9f8db0` |
| `site_data/candidates_moon_lat20-40_connecting_ridge_c1__power_night.geojson` | 241680 | `f36d78b076a3d7ffb986717638f405f874acfe694d0eee23fbca44bf9419dd16` |
| `site_data/candidates_moon_lat20-40_shackleton_rim__base.csv` | 78294 | `55d7bcb1e9c149d268da62948e57216ce7a8dbe8db0f3d7831f009472f227ea0` |
| `site_data/candidates_moon_lat20-40_shackleton_rim__base.geojson` | 240704 | `11d356b3bb1327295ce5d0b62d2f2c5cda26a4374efeeaeeabb3ef54fb019212` |
| `site_data/candidates_moon_lat20-40_shackleton_rim__landing_mobility.csv` | 76797 | `acf23af53585ab69dd6319eb692745e9413d7b483fb38e576ee47f783691a667` |
| `site_data/candidates_moon_lat20-40_shackleton_rim__landing_mobility.geojson` | 239171 | `0217b8f26ff438ff22fe10fdd387f93d3718d325d783d7ef3a77b8e8f260d966` |
| `site_data/candidates_moon_lat20-40_shackleton_rim__power_night.csv` | 78346 | `492baabc25be8d81528d7ac77edbcfa8fb260f5757c4ca4b8b5912a140d3cebb` |
| `site_data/candidates_moon_lat20-40_shackleton_rim__power_night.geojson` | 240753 | `d2a12862c1bf99772772f08c63063cb0ed7681d22a399abe86f946aa4929e9fb` |
| `site_data/candidates_moon_shackleton_rim__base.csv` | 80573 | `104ddc1dc713143f1ac2c08efedd8ec56d3121e58a97fafa164ee783efc23028` |
| `site_data/candidates_moon_shackleton_rim__base.geojson` | 242980 | `91268c9411fbdfb223b8346fe50f042174939f39d6ba018fa7793c7a91f050ca` |
| `site_data/candidates_moon_shackleton_rim__landing_mobility.csv` | 77966 | `8040ab94436c11052bb2073e91ff0a6287699dbb360b985e84a1bbcd93dfe34f` |
| `site_data/candidates_moon_shackleton_rim__landing_mobility.geojson` | 240358 | `02438633f611d572c2b132e933ef5139dfe6b010f83d7fcab867e9292e90ed82` |
| `site_data/candidates_moon_shackleton_rim__power_night.csv` | 80578 | `ca38b8ad3f1867d2f06383b9ed4de56615f772ee2f46730f74ff2e8b0e5c1906` |
| `site_data/candidates_moon_shackleton_rim__power_night.geojson` | 242976 | `b12dc155dbe87b165fa08f61a6e456200617987cdfac5782a10f981365f2880e` |
| `site_data/india_boundary_naturalearth_ind_10m.geojson` | 343199 | `b9837bcfb8f26a5182ff2c8d3a39d89164c523eb2f4c05d558fad0f8085c5d4f` |
| `site_data/india_mars_jezero__base.csv` | 10149 | `542369f4e6f27b7f1ad02285bdd7bf5024eefe07703c2fec1b48ad6e4a2a731b` |
| `site_data/india_mars_jezero__ice_resources.csv` | 10149 | `542369f4e6f27b7f1ad02285bdd7bf5024eefe07703c2fec1b48ad6e4a2a731b` |
| `site_data/india_mars_jezero__landing_mobility.csv` | 10144 | `b6ae0019884c03213be2bc24e4efb6f73827d4e71b8ad8a5ac0596b47a253d91` |
| `site_data/india_mars_jezero__power_night.csv` | 10164 | `c6091011674cbf3dd75a8fb353da8ed7d195f738e9b4ef592f51f9554a1efc1c` |
| `site_data/india_moon_connecting_ridge_c1__base.csv` | 10668 | `3993194e5bc544fc6507afdabbd6127a2218e0ca57970c537ccee1fd2f2a0cdf` |
| `site_data/india_moon_connecting_ridge_c1__landing_mobility.csv` | 10739 | `bc0b6d233686832a6bea1aa4fb4ab35d7bdf045762c6c40ecf660a2bd25e8112` |
| `site_data/india_moon_connecting_ridge_c1__power_night.csv` | 10660 | `4367ff9c0d67eba444c7e08bf0b6b1006dc02ccd71b1de7cbc7214ba21dfacba` |
| `site_data/india_moon_lat20-40_connecting_ridge_c1__base.csv` | 10661 | `c4cb90b89dfb7195623179c3839fa63a9c9a09f3653736571664c5533f7594d2` |
| `site_data/india_moon_lat20-40_connecting_ridge_c1__landing_mobility.csv` | 10737 | `f3bf48b2674802a06a3b7e42157f732252188626d7f419011f30dfaee5b51648` |
| `site_data/india_moon_lat20-40_connecting_ridge_c1__power_night.csv` | 10654 | `2377c4b645576e1bf35aa405ac69cd6188073c1af1658d02f7a84d079aa4c923` |
| `site_data/india_moon_lat20-40_shackleton_rim__base.csv` | 10795 | `684635c111585885ebd79db183f49a7e31318bf7408f48d0bbf65b5a445bf0e2` |
| `site_data/india_moon_lat20-40_shackleton_rim__landing_mobility.csv` | 10709 | `9e402c9da4f4f4889c3ebd482842315d71949c72e0b84f275bb79aa411f92468` |
| `site_data/india_moon_lat20-40_shackleton_rim__power_night.csv` | 10800 | `3f699b07903395d3dc33a8a46e6fa955096fe2788cb6390c7bd130261b2999c7` |
| `site_data/india_moon_shackleton_rim__base.csv` | 10800 | `9ef1b8a143ae6082bc151a7640f583787a36ffbbe7719ee0e59d733c01570d02` |
| `site_data/india_moon_shackleton_rim__landing_mobility.csv` | 10704 | `8eed4d1386ef5fbe74e3755b6b7a7b474be24c9a667dc04de347154d5cc6f405` |
| `site_data/india_moon_shackleton_rim__power_night.csv` | 10805 | `79e67fee959cf2b1fe90cc0a3c73869cac73fd972bd3ca856fe0ef9d1dcdfcf6` |
| `site_data/limits_mars.json` | 9024 | `ce8043351d02793ac04ed1b51085eb97da0608ba3ea1eba692c12f6c59d68254` |
| `site_data/limits_moon.json` | 10856 | `9b6264fcb147330a051d44110cf3ae4176e1a3a7499db248ee4d729ceeb3b824` |
| `site_data/limits_moon_lat20-40.json` | 10856 | `9b6264fcb147330a051d44110cf3ae4176e1a3a7499db248ee4d729ceeb3b824` |
| `site_data/run_summary.json` | 18355 | `77409acd7f28d5253a93fd547f79168d5cfdba87cf6f06b1cae19b3f9ae48ada` |
| `site_data/validation_summary_mars.json` | 3023 | `f5a0cc8d17c6eab576cd867572c9586c0294a52fe452131906d22668cd9e2b23` |
| `site_data/validation_summary_moon.json` | 2903 | `7f59940b60d53192677376948debb52994d305e80d94fe1cd43d4090187c8f71` |
| `site_data/validation_summary_moon_lat20-40.json` | 2965 | `6d2cc5fe1e7513e5b6c5ce753b1c7b5153d3f2f744f1fb34df8d137e1cedb1dc` |
