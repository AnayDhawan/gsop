# Natural Earth layers for region names

Used only to put a place name on each region (decision for B12). Labels only: no score uses these files.

- Source: Natural Earth vector data, release v5.1.2, GeoJSON copies from https://github.com/nvkelso/natural-earth-vector (scale 1:10m).
- Licence: public domain. Credit: "Made with Natural Earth."
- Raw files, as downloaded (not committed):
  - `ne_10m_geography_regions_polys.geojson`, sha256 `b7b26e50ea917d3696aec87f932def2bf5f890f5770e441d59c162c6f4c92a77`
  - `ne_10m_populated_places_simple.geojson`, sha256 `fd3fa867a320cbd5c5b6bb5bc550afeec2939fb2cef688e508007282a55ac42f`
- Committed files (trimmed by `scripts/gsop_data/naturalearth_prep.py`, so the build needs no network):
  - `regions_desert_plateau_range.geojson`: only the Desert, Plateau and Range/mtn polygons (352 features), name and class kept, coordinates rounded to 4 decimals.
  - `populated_places.csv`: populated places and capitals (7,295 rows), name, country, lat, lon. Scientific stations, historic places and weather stations are left out.
- Natural Earth boundaries and names are generalised and not authoritative. A name here is a label for orientation, not a claim about the ground.
