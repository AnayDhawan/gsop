// Shapes of the files under public/data (see docs/DATA_CONTRACT.md).
export type Meta = {
  schema_version: number;
  file: string;
  label: string;
  limits: string[];
  sources: { source_file: string; sha256: string }[];
  facts?: { claim: string; number: string; source_file: string; sha256: string }[];
  uncertainty_sentence?: string;
  [k: string]: unknown;
};

export type Body = "Moon" | "Mars";

export type Site = {
  id: string; // build key: slug plus body
  slug: string;
  name: string;
  body: Body;
  list: "known" | "candidate";
  country: string | null;
  lat: number;
  lon: number;
  elevation_m: number | null;
  why_analog: string | null;
  key_differences: string | null;
  experiments_done: string | null;
  experiments_possible: string | null;
  how_to_modify: string | null;
  year_first_used_as_analog: number | null;
  status: string;
  sources_ok: boolean;
  source_note: string;
  origin: string;
  coord_source: string;
  v1_used: boolean | null;
  v1_match: { site_id: string; km: number };
  kind: string | null;
  analog_of: string | null;
  region: string | null;
  summary: string | null;
  terrain_geology: string | null;
  climate: string | null;
  parameters_matched: string | null;
  access_and_facilities: string | null;
  hazards: string | null;
  source_url_1: string | null;
  source_url_2: string | null;
  source_url_3: string | null;
};

export type LookupEntry =
  | { status: "scored"; tile_id: number; km_to_tile: number; score: number; percentile: number; top5_in_90pct_runs: boolean; source_file: string; sha256: string }
  | { status: "gated_out" | "missing_data" | "no_land_tile"; reason: string; source_file: string; sha256: string };

export type SummaryGroup = { n: number; n_group: number; median_percentile?: number | string };

export type TileRow = {
  tile_id: number;
  lat: number;
  lon: number;
  score: number;
  mc_median: number;
  mc_p05: number;
  mc_p95: number;
  freq_top5: number;
  top5_in_90pct_runs: boolean;
  illum_match: number;
  in_india: boolean | string;
  nearest_reference_site?: string;
  km_to_nearest_reference_site?: number;
};

export type View = {
  target: string;
  profile: string;
  body: "moon" | "mars";
  confidence: string;
  illum_match_family: string;
  n_gated_tiles: number;
  n_top5_in_90pct_runs: number;
  tiles: TileRow[];
};

export type Region = {
  id: string;
  target: string;
  body: "moon" | "mars";
  confidence: string;
  n_tiles: number;
  area_km2: number;
  centroid_lat: number;
  centroid_lon: number;
  bbox: { south: number; north: number; west: number; east: number };
  median_score: number;
  median_mc_median: number;
  km_to_nearest_reference_site: number;
  nearest_reference_site: string;
  n_tiles_in_india: number;
  place: { name: string; feature_class: string; relation: "inside" | "near" | "nearest populated place"; distance_km: number; source: string };
  status: string;
  caveat: string;
};

export type Metric = {
  id: string;
  group: string;
  label: string;
  unit: string;
  value: number | string;
  display: string;
  source_file: string;
  sha256: string;
  what_this_means_for_the_analogy: string;
};

export type LedgerEntry = {
  id: string;
  type: "failed_control" | "known_limit" | "unscored_property" | "physical_difference";
  body: string;
  status: string;
  provisional: boolean;
  statement: string;
  source?: string;
  source_file: string;
  sha256: string;
  what_this_means_for_the_analogy: string;
};

export type Overlay = {
  meta: Meta;
  target: string;
  body: "moon" | "mars";
  confidence: string;
  image: string;
  bounds: { west: number; south: number; east: number; north: number };
  width: number;
  height: number;
};

export type Control = {
  id: string;
  label: string;
  lat: number;
  lon: number;
  coordinates_confirmed: boolean;
  runs: Record<string, { status: string; rank_pct?: number; reason?: string }>;
};
