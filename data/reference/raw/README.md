# Raw reference data

`GSOP_analog_sites_moon_mars.csv`: LLM-estimated, not simulation output.

- 120 rows: Moon 50 known + 10 candidates, Mars 50 known + 10 candidates.
- It has no source URLs. Similarity percentages, P_* scores, Monte Carlo bounds and rank ranges are model guesses and must never appear on the site or in `claims.csv`.
- The file is kept untouched. Loaded into Supabase by `scripts/push_sites_csv.py`; column mapping in `docs/sites_mapping.md`.
