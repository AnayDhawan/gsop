# CLAUDE.md: GSOP site

Website for GSOP (Geospatial Similarity Observation Platform), built for NASA Space Apps Challenge 2026. The simulation lives in a separate repo (`AnayDhawan/sim`). This repo only presents its v1 results.

## Hard rules
- **No new simulation.** The site reads v1 outputs. It never recomputes scores.
- **Every number on the site comes from a data file in `data/` and a row in `claims.csv`.** No number typed by hand into a page, script or submission text.
- **Plain layouts in Phases A to E.** Design starts in Phase F. Do not polish early.
- Work is tracked in GitHub issues `[A1]` to `[F12]`, grouped by milestone (Phase A to F). Read the issue's "Needs" and "Done when" before starting.

## Wording rules (decision E32)
- Say "candidates not in our reference list". Never "discovered", "undiscovered", "new sites" or "validated".
- Mars is a low-confidence secondary result.
- Show the failed negative-control test openly.
- Print the E32 uncertainty sentence verbatim next to the results. Source text: `docs/E32.txt`.
- Headline direction: a transparent, reproducible screening method with an India focus, and what it can and cannot tell us.
- Say plainly that the ranking is not validated.

## Writing rules
- No em dashes anywhere (code comments, docs, commits, UI text). Use commas, colons, semicolons, periods or parentheses.
- No AI-slop vocabulary (delve, robust, seamless, leverage, unlock, showcase, and similar).
- No `Co-Authored-By` trailer and no AI attribution in commits or PRs.
- Sentence case in headings. Bullets over prose.

## Stack
- Next.js 16 (App Router), React 19, Tailwind 4, TypeScript, vitest. Node 24.
- Theme tokens live in `src/app/globals.css`. Rename nothing, change values only (A6 locks them).
- Read `node_modules/next/dist/docs/` before using a Next.js API you are unsure about; this version differs from older releases.

## Commands
- `npm run dev`, `npm run build`, `npm run lint`, `npm test`

## People
- Anay (`AnayDhawan`): decisions, design, review. Yash (`yakew7`): code and content.
- Issues owned by Anay are kept cheap: no Claude Code, or one short session.

## Data
- Raw v1 results are not committed. They arrive as a zip from Anay; B1 inventories and hashes them.
- Generated data files are listed in `MANIFEST.csv` with sha256 hashes (issue B5).

- (h) Supabase is the edit store for the 50-site table only. The deployed site reads exported static JSON and never calls Supabase at runtime. The service key lives only in a local .env, never committed.
