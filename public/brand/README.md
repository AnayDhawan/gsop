# GSOP brand assets

**GSOP — Geospatial Similarity Observation Platform** compares locations on Earth with candidate locations on the Moon and Mars. This folder is the complete production brand library: 40 asset families, design tokens, self-hosted fonts, a JSON manifest and a master preview page.

- Open **`brand-preview.html`** to see every asset (light/dark toggle, filter, copy-path).
- Open **`guidelines/gsop-brand-guidelines-overview.html`** (or the PNG / PDF) for the one-page guidelines.
- `brand-assets.json` lists every file with format, dimensions, theme, usage and relative path.

Drop the folder into a web project as `public/brand/` (paths below assume the site serves it at `/brand/`).

## Brand summary

A calm, precise **survey-instrument** identity: contour lines, graticules, dot-matrix, registration marks and machined (square / chamfered) borders on deep-black or soft-grey surfaces. Three planets — **Moon, Earth, Mars** — carry the identity; the **signature motif** is three luminous dot-grid ribbons (Moon white-grey, Earth blue-green, Mars muted red) that cross in gentle S-curves. The ribbons are used for emphasis and are deliberately *not* in every asset.

## Logo usage

| Variant | File (in `logos/`) | Use on |
|---|---|---|
| Horizontal · dark | `gsop-logo-horizontal-dark.svg` | dark surfaces (default header/footer) |
| Horizontal · light | `gsop-logo-horizontal-light.svg` | light surfaces |
| Stacked · dark / light | `gsop-logo-stacked-{dark,light}.svg` | square or narrow spaces |
| Symbol · dark / light | `gsop-symbol-{dark,light}.svg` | avatars, compact UI (≥ 48 px) |
| Monochrome | `gsop-logo-mono-{white,dark}.svg` | single-colour reproduction |
| Editable text source | `gsop-logo-*-{dark,light}.text-source.svg` | live-text (Space Grotesk / JetBrains Mono) version for design tools; the standard files use outlined lettering |

Rules: planets in the order **Moon · Earth · Mars**; three equal diameters with a slight overlap; **Earth is in front and overlaps both neighbours** and is always fully opaque and sharp; the wordmark is Space Grotesk capitals; the descriptor `GEOSPATIAL SIMILARITY OBSERVATION PLATFORM` is JetBrains Mono, small and tracked. **Clear space** = ½ planet diameter on every side. **Minimum widths**: horizontal with descriptor 400 px · horizontal wordmark only 160 px · stacked 200 px · symbol 48 px (below that use the favicon symbol). See `logos/gsop-logo-construction-guide.*` and `logos/gsop-logo-misuse-reference.*`. Use one logo per view — do not add a second header logo.

## Colours

Planetary colours are identical in both themes and are never inverted.

| Token | Hex | Role |
|---|---|---|
| `--gsop-lunar-grey` | #A9ADB1 | Moon · secondary text on dark |
| `--gsop-earth-blue` | #287DB5 | Earth oceans · focus · primary data |
| `--gsop-earth-green` | #24865F | Earth land · positive state |
| `--gsop-martian-red` | #B84B3A | Mars · mismatch · alert |
| `--gsop-void-black` | #06080A | Dark background |
| `--gsop-deep-graphite` | #0D1114 | Dark surface |
| `--gsop-basalt` | #1B2024 | Raised surface |
| `--gsop-technical-grey` | #737C83 | Muted text, ticks |
| `--gsop-hairline-grey` | #30383D | Dark borders |
| `--gsop-off-white` | #ECEDE8 | Text on dark |

Theme roles — **dark**: background #06080A · surface #0D1114 · text #ECEDE8 · secondary #A9ADB1 · border #30383D. **Light**: background #F4F5F3 · surface #FFFFFF · text #171C20 · secondary #626B72 · border #D8DDE0.

## Typography

| Family | Use | Weights |
|---|---|---|
| **Space Grotesk** | logo, headings | 500 · 600 · 700 |
| **Inter** | body copy | 400 · 500 · 600 |
| **JetBrains Mono** | technical labels, descriptor | 400 · 500 |

The fonts above are **self-hosted** in `fonts/` (WOFF2, Latin subset, SIL Open Font License 1.1 — licence texts included) and declared with `@font-face` in `brand-tokens.css`. Only those weights are shipped; other characters and weights fall back to the system stacks in the tokens. Logo and wordmark artwork do not depend on any font (outlined).

## Directory structure

```
public/brand/
├─ brand-tokens.css        design tokens + theme roles
├─ brand-assets.json       manifest of every file
├─ brand-preview.html      master preview of all 40 families
├─ README.md
├─ fonts/                  self-hosted WOFF2 + OFL licences
├─ logos/                  families 01–10
├─ favicons/               families 11–14 (+ manifest, browserconfig)
├─ app-icons/              families 15–16
├─ og/                     family 17
├─ social/                 families 21–23
├─ motifs/                 ribbon, graticule, fingerprint, ring, comparison, hero, footer, loader (18–20, 24, 25, 28–31)
├─ patterns/               contour pattern, point cloud (26–27)
├─ icons/
│  ├─ scientific/  planetary/  navigation/   individual SVGs + sheets (33–35)
│  └─ gsop-icons-sprite.svg, gsop-icon-construction-sheet-*.svg
├─ components/             badge, headers, attribution, disclaimer, divider (32, 36–39)
├─ guidelines/             family 40 (HTML · PNG · PDF)
└─ examples/               head metadata + Next.js layout
```

Naming: lowercase kebab-case, `gsop-<asset>-<variant>-<theme>[-<size>].<ext>`. SVG for vector art, PNG for raster/social, ICO for favicons, WebP for optimised photographic imagery (hero, footer, comparison), CSS for tokens, JSON for the manifest.

## Theme implementation

```html
<link rel="stylesheet" href="/brand/brand-tokens.css">
<html lang="en" data-theme="dark">  <!-- or "light"; omit to follow the OS -->

<img class="gsop-logo gsop-logo--dark"  src="/brand/logos/gsop-logo-horizontal-dark.svg"  alt="GSOP — Geospatial Similarity Observation Platform">
<img class="gsop-logo gsop-logo--light" src="/brand/logos/gsop-logo-horizontal-light.svg" alt="" aria-hidden="true">
```

`brand-tokens.css` maps the colours to roles (`--gsop-bg`, `--gsop-surface`, `--gsop-text`, `--gsop-text-secondary`, `--gsop-border`) per `data-theme`, and hides whichever logo does not match. Toggle with `document.documentElement.dataset.theme = 'light' | 'dark'`.

## Favicon integration

```html
<link rel="icon" href="/brand/favicons/favicon.ico" sizes="any">
<link rel="icon" href="/brand/favicons/favicon-dark.svg"  type="image/svg+xml" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/brand/favicons/favicon-light.svg" type="image/svg+xml" media="(prefers-color-scheme: light)">
<link rel="icon" href="/brand/favicons/favicon-dark-32x32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/brand/favicons/apple-touch-icon.png">
<link rel="mask-icon" href="/brand/favicons/safari-pinned-tab.svg" color="#06080A">
<link rel="manifest" href="/brand/favicons/site.webmanifest">
<meta name="msapplication-config" content="/brand/favicons/browserconfig.xml">
<meta name="theme-color" content="#06080A" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#F4F5F3" media="(prefers-color-scheme: light)">
```

## Open Graph & social metadata

```html
<meta property="og:type" content="website">
<meta property="og:site_name" content="GSOP">
<meta property="og:title" content="GSOP — Geospatial Similarity Observation Platform">
<meta property="og:description" content="Compare locations on Earth with candidate locations on the Moon and Mars.">
<meta property="og:image" content="https://YOUR-DOMAIN/brand/og/gsop-og-image-1200x630.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Moon, Earth and Mars">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://YOUR-DOMAIN/brand/og/gsop-og-image-1200x630.png">
```

The OG image contains **only** the Moon (left), Earth (centre) and Mars (right) on a sparse black starfield — no text, logo, ribbons, frames or UI. Use absolute URLs for `og:image`. A 2400 × 1260 master is in `og/`.

## Using the SVG icons

All 28 icons use a 24 × 24 grid, 1.5 px stroke, mitered joins (limit 2) and `currentColor`, so they take the surrounding text colour.

```html
<!-- inline sprite (recommended): colour with CSS -->
<svg class="gsop-icon" aria-hidden="true"><use href="/brand/icons/gsop-icons-sprite.svg#gsop-icon-search"/></svg>

<!-- single file via <img>: renders in the default colour (use CSS mask to tint) -->
<img src="/brand/icons/navigation/gsop-icon-search.svg" width="24" height="24" alt="">
```

Cross-file `<use>` requires same-origin hosting; otherwise paste the sprite inline once. The *Earth site marker* is the only two-colour icon (blue + green). Meaning is never carried by colour alone — mismatch is always hatched.

## Raster vs vector

| Need | Use |
|---|---|
| Logos, icons, ribbons, patterns, components | SVG (PNG provided for tools that cannot read SVG) |
| Social cards, OG, app icons | PNG |
| Browser tab icons | ICO + SVG + PNG |
| Hero, footer, comparison (photographic planets) | WebP first, PNG fallback |

Planet surfaces inside SVG files (logos, favicons, app icons, headers, loader) are the same renders as the hero and OG imagery, embedded as JPEG images; the wordmark and descriptor are always vector outlines. The monochrome logos use the planet renders as soft tone maps (a mask filled with one colour), so craters and surface features blend in instead of being cut out as solid shapes; change the single `fill` on the mask rectangles to recolour them. `favicons/safari-pinned-tab.svg` is pure flat vector, as Safari requires.

## Next.js example

See `examples/nextjs-layout.tsx` (App Router metadata + viewport) and `examples/head-metadata.html`.

## Provenance & notes

- Planet artwork is rendered for this project: continent outlines come from Natural Earth (public domain); Moon and Mars surfaces are procedurally generated (soft albedo regions, shaded craters, Valles Marineris and polar-cap detail on Mars) and stylised. **No NASA or other agency imagery is used**, and the artwork is illustrative, not scientific data.
- The dataset-attribution component is a template — replace each field per dataset.
- GSOP is an independent project and is not affiliated with or endorsed by NASA; use `components/gsop-disclaimer-lockup-*` where appropriate.

## Asset index (169 files in 40 families)

| # | Family | Files |
|---|---|---|
| 01 | A · Horizontal logo — dark | 3 |
| 02 | A · Horizontal logo — light | 3 |
| 03 | A · Stacked logo — dark | 3 |
| 04 | A · Stacked logo — light | 3 |
| 05 | A · Symbol — dark | 2 |
| 06 | A · Symbol — light | 2 |
| 07 | A · Monochrome logo — white | 2 |
| 08 | A · Monochrome logo — dark | 2 |
| 09 | A · Logo construction & clear-space guide | 2 |
| 10 | A · Logo misuse reference | 2 |
| 11 | B · Favicon 16 — dark | 2 |
| 12 | B · Favicon 32 — dark | 1 |
| 13 | B · Favicon 64 — dark, ICO & manifest | 5 |
| 14 | B · Light-mode favicon family | 5 |
| 15 | B · App icon 1024 — dark | 6 |
| 16 | B · App icon 1024 — light | 2 |
| 17 | C · Open Graph image | 2 |
| 18 | C · Website hero — dark | 2 |
| 19 | C · Website hero — light | 2 |
| 20 | C · Website footer | 2 |
| 21 | C · Social image — square | 1 |
| 22 | C · Social image — landscape | 1 |
| 23 | C · GitHub banner | 1 |
| 24 | C · Loading visual | 3 |
| 25 | D · Signature ribbon | 4 |
| 26 | D · Topographic contour pattern | 4 |
| 27 | D · Point-cloud texture | 2 |
| 28 | D · Geospatial graticule | 6 |
| 29 | D · Planetary comparison illustration | 4 |
| 30 | D · Seven-bar similarity fingerprint | 8 |
| 31 | D · Confidence ring | 6 |
| 32 | D · Scientific data badge | 4 |
| 33 | E · Scientific icons | 15 |
| 34 | E · Planetary & map icons | 11 |
| 35 | E · Navigation & utility icons | 19 |
| 36 | F · Planetary information header | 8 |
| 37 | F · Dataset attribution component | 4 |
| 38 | F · Independent-project disclaimer lockup | 8 |
| 39 | F · Section divider | 4 |
| 40 | F · Brand guidelines overview sheet | 3 |
