# Site decisions (issue A6)

## Locked
- **Name:** GSOP. Full name: Geospatial Similarity Observation Platform.
- **Theme tokens:** the GSOP brand pack. Tokens live in `src/app/globals.css` with the `--gsop-*` names, assets in `public/brand`. Dark is the default theme; light is available through `data-theme`.
- **Fonts:** Space Grotesk (headings), Inter (body), JetBrains Mono (labels). Self-hosted.
- **Controls on the Honest Map:** Martian red (`--gsop-martian-red`, utility `text-control`).
- **Wording (decision E32):** say "candidates not in our reference list". Never "validated", "discovered", "undiscovered" or "new sites". Mars is a low-confidence secondary result. The failed negative-control test is shown openly. The ranking is not validated.

## Headline (proposed, Anay to confirm)
Direction from E32: a transparent, reproducible screening method with an India focus, and what it can and cannot tell us.

Proposed line: **A transparent screening method for Earth places that resemble the Moon and Mars.**

Proposed support line: **Open data, open method, and a plain account of what it cannot tell you.**

Change these two lines here, then C4 (landing page) follows this file.

## Open
- Production domain: not chosen. Current deployment: https://gsoplatform.vercel.app
