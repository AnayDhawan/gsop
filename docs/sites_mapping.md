# Sites CSV column mapping

Source: `data/reference/raw/GSOP_analog_sites_moon_mars.csv` (37 columns, 120 rows). The CSV is LLM output. All 37 columns are kept as-is in `public.sites_llm_raw` (one jsonb row per CSV row). Only the mapped columns below reach `public.sites`.

## Mapped to sites

| CSV column | sites column | Rule |
|---|---|---|
| Body | body | Moon or Mars, as written |
| Category | list | "Known (top 50)" becomes `known`, "New candidate (low-profile)" becomes `candidate` |
| Site_name | name, slug | slug is ascii-lowercase-hyphen of the name; same-body collision gets -2; same name on both bodies gives the same slug on purpose |
| Country | country | verbatim |
| Latitude, Longitude | lat, lon | float; blank, unparseable, out of range or (0,0) becomes null on both plus coord_flag `bad` |
| Coordinate_note | coord_source | contains "approx" gives `csv_approx`, else `csv` |
| Elevation_m | elevation_m | number |
| Justification | why_analog | verbatim, banned-word rewrites only |
| Where_analogy_breaks | key_differences | verbatim, banned-word rewrites only |
| Experiments_conducted | experiments_done | verbatim, banned-word rewrites only |
| Experiments_that_can_be_conducted | experiments_possible | verbatim, banned-word rewrites only |
| How_to_modify_artificially | how_to_modify | verbatim, banned-word rewrites only |
| First_used_as_analog | year_first_used_as_analog | leading 4-digit year, else null; the original text is also kept in notes |
| Discovered_or_recognised | notes | internal only, never exported |
| Prior_analog_use | notes | internal only, never exported |

Fixed values on every row: origin `llm_csv`, status `draft`, sources_ok `false`, source_url_1 to 3 null, source_note `no sources in CSV`, v1_used null.

## Raw only (never reach sites)

| CSV column | Why |
|---|---|
| Rank_in_category | LLM ranking, not a result |
| Similarity_pct | LLM estimate, not simulation output |
| MonteCarlo_5th_pct, MonteCarlo_95th_pct, MC_rank_range_of_60 | LLM estimates presented as simulation output |
| Parameter_similarity_summary | repeats the P_* scores |
| P_slope, P_illumination_or_sunlight, P_colddry_or_water_ice, P_roughness, P_relief, P_temperature, P_composition, P_thermal_inertia, P_air_density_Mars_only | LLM estimated scores |
| GSOP_gate_check | LLM estimate of a simulation gate |
| Nearest_known_analog_site, Nearest_known_km, Passes_100km_novelty_rule | LLM estimates; recomputed in `sites_check.md` for the 20 candidates |
| Scored_against | describes the LLM's imagined scoring target |

## AMBIGUOUS (no confident target, kept out of sites)

| CSV column | Why |
|---|---|
| Process_type | Free text such as "Impact (23 km) in polar desert". Could be `kind` or `terrain_geology`. The text is copied into notes (internal) so nothing is lost; kind and terrain_geology stay null until a human decides. |

## No CSV column, left null

kind, analog_of, region, summary, terrain_geology, climate, parameters_matched, access_and_facilities, hazards, source_url_1 to 3, v1_used.
