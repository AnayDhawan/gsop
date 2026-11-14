# Natural Earth raw files

Used only to put a place name on each region (decision B12). Labels only: no score uses these files.

- Source: Natural Earth vector data, release v5.1.2, GeoJSON copies from https://github.com/nvkelso/natural-earth-vector (scale 1:10m). Downloaded 15 Nov 2026.
- Licence: public domain. Credit: "Made with Natural Earth."
- Files, unmodified, with their sha256 (also in `data/MANIFEST.csv`):
  - `ne_10m_geography_regions_polys.geojson`: `b7b26e50ea917d3696aec87f932def2bf5f890f5770e441d59c162c6f4c92a77`
  - `ne_10m_populated_places_simple.geojson`: `fd3fa867a320cbd5c5b6bb5bc550afeec2939fb2cef688e508007282a55ac42f`
- How they are used (`scripts/gsop_data/naming.py`): only the Desert, Plateau and Range/mtn polygons, and the populated places and capitals. Other classes in the files are ignored.
- Natural Earth boundaries and names are generalised and not authoritative. A name is a label for orientation, not a claim about the ground.
