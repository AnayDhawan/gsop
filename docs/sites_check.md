# Sites CSV check

Source: `data/reference/raw/GSOP_analog_sites_moon_mars.csv`. The CSV is LLM output. Scores in it are estimates, not simulation output. This file lists problems and changes nothing.

## Counts by body and list

| Body | List | Rows | Expected |
|---|---|---|---|
| Moon | known | 50 | 50 |
| Moon | candidate | 10 | 10 |
| Mars | known | 50 | 50 |
| Mars | candidate | 10 | 10 |

Total: 120

## Coordinates

- Rows flagged coord_flag='bad' (blank, unparseable, out of range or 0,0): 0
- Approximate coordinates (Coordinate_note contains 'approx'): 60 (expected about 60)
- Same-body points within 1 km: 0

## Same slug on both bodies (one page, two sections by design)

- Count: 1
  - hi-seas-habitat-mauna-loa

## Possible merges (similar names across bodies, no auto-merge)

- Pairs with name similarity >= 0.75 and different slugs: 3
  - 1.00: Moon row 34 Mars Desert Research Station (lunar crews) / Mars row 79 Mars Desert Research Station (Hanksville)
  - 1.00: Moon row 41 Lonar crater / Mars row 99 Lonar crater (Mars context)
  - 0.76: Moon row 22 Kilauea caldera and Ka'u Desert / Mars row 74 Kilauea Ka'u Desert (BASALT)

## Candidate novelty check (nearest known site, haversine over all 100 known rows)

Tolerance 2 km against the CSV's Nearest_known_km. Known rows without coordinates are skipped.

| Row | Candidate | Body | CSV nearest | CSV km | Recomputed nearest | Recomputed km | Diff km | Note |
|---|---|---|---|---|---|---|---|---|
| 51 | Peary Land polar desert (central plateau) | Moon | Bockfjord Volcanic Complex (AMASE) | 841 | Bockfjord Volcanic Complex (AMASE) | 841 | 0 | ok |
| 52 | Mount Howe and the Scott Glacier moraines (southernmost rock) | Moon | Beacon Valley and University Valley (Dry Valleys) | 1187 | Beacon Valley and University Valley (Dry Valleys) | 1187 | 0 | ok |
| 53 | Bunge Land (Zemlya Bunge) | Moon | Kolyma Lowland permafrost | 911 | Kolyma Lowland permafrost | 911 | 0 | ok |
| 54 | Schirmacher Oasis (near Maitri station) | Moon | Lake Untersee (astrobiology analog) | 93 | Vostok Station | 2581 | 2488 | DIFF |
| 55 | Fiskenaesset anorthosite complex (Qeqertarsuatsiaq) | Moon | Mistastin (Kamestastin) Lake crater | 1068 | Mistastin (Kamestastin) Lake crater | 1068 | 0 | ok |
| 56 | Payun Matru volcanic field and Pampas Onduladas flow | Moon | Salar de Pajonales | 1254 | Salar de Pajonales | 1254 | 0 | ok |
| 57 | Karakul impact structure (Pamir) | Moon | Ladakh - Tso Kar and Puga | 754 | Ladakh - Tso Kar and Puga | 754 | 0 | ok |
| 58 | Harrat Khaybar and Umm Jirsan lava tube | Moon | Makhtesh Ramon (D-MARS, AMADEE-20) | 750 | Makhtesh Ramon (D-MARS, AMADEE-20) | 750 | 0 | ok |
| 59 | Tenoumer crater | Moon | Lanzarote - Timanfaya and La Corona lava tube | 755 | Lanzarote - Timanfaya and La Corona lava tube | 755 | 0 | ok |
| 60 | Kamil crater | Moon | Makhtesh Ramon (D-MARS, AMADEE-20) | 1290 | Makhtesh Ramon (D-MARS, AMADEE-20) | 1290 | 0 | ok |
| 111 | Ojos del Salado high-altitude permafrost | Mars | Salar de Pajonales | 220 | Salar de Pajonales | 220 | 0 | ok |
| 112 | Emi Koussi volcano (Tibesti) | Mars | Makhtesh Ramon (D-MARS, AMADEE-20) | 2025 | Makhtesh Ramon (D-MARS, AMADEE-20) | 2025 | 0 | ok |
| 113 | Lop Nur 'Great Ear' salt crust | Mars | Kumtag Desert (Yutu rover tests, Dunhuang) | 178 | Kumtag Desert (Yutu rover tests, Dunhuang) | 178 | 0 | ok |
| 114 | Samail Ophiolite - Wadi Tayin massif | Mars | Dhofar desert (AMADEE-18) | 546 | Dhofar desert (AMADEE-18) | 546 | 0 | ok |
| 115 | Bodele Depression (diatomite deflation basin) | Mars | Makhtesh Ramon (D-MARS, AMADEE-20) | 2292 | Makhtesh Ramon (D-MARS, AMADEE-20) | 2292 | 0 | ok |
| 116 | Dasht-e Lut - Kalut yardang field | Mars | Dhofar desert (AMADEE-18) | 1305 | Dhofar desert (AMADEE-18) | 1305 | 0 | ok |
| 117 | Umm al Samim sabkha | Mars | Dhofar desert (AMADEE-18) | 307 | Dhofar desert (AMADEE-18) | 307 | 0 | ok |
| 118 | Lake Abbe hydrothermal carbonate chimneys | Mars | Dallol | 384 | Dallol | 384 | 0 | ok |
| 119 | Gilf Kebir plateau and wadis | Mars | Makhtesh Ramon (D-MARS, AMADEE-20) | 1199 | Makhtesh Ramon (D-MARS, AMADEE-20) | 1199 | 0 | ok |
| 120 | Chott el Djerid | Mars | ESA CAVES site (Sa Grutta, Sardinia) | 736 | ESA CAVES site (Sa Grutta, Sardinia) | 736 | 0 | ok |

Candidates needing review: 1

## Empty-field counts (sites columns mapped from the CSV)

| Column | Empty of 120 |
|---|---|
| name | 0 |
| body | 0 |
| list | 0 |
| slug | 0 |
| country | 0 |
| lat | 0 |
| lon | 0 |
| elevation_m | 0 |
| why_analog | 0 |
| key_differences | 0 |
| experiments_done | 0 |
| experiments_possible | 0 |
| how_to_modify | 0 |
| year_first_used_as_analog | 63 |
| notes | 0 |

Columns with no CSV equivalent stay null: kind, analog_of, region, summary, terrain_geology, climate, parameters_matched, access_and_facilities, hazards, elevation source.

## Banned-word rewrites applied to public columns

Wording rule E32. Only the agreed rewrites were applied. Original text stays in sites_llm_raw. Capitalisation of the first letter was kept for field-measured.

- row 33 column why_analog: `Apollo-validated`
- row 35 column why_analog: `Apollo-validated`
- row 60 column why_analog: `find new sites`
- row 116 column experiments_possible: `Field-validated`
