## Project Name

GSOP: Geospatial Similarity Observation Platform

## High-Level Project Summary

GSOP is an open, reproducible screening method that scores every land tile on Earth by how closely its terrain matches lunar and Martian targets, with an India focus. Its main result is honest: the method failed its own negative-control test, so it ranks places worth a closer look, not places confirmed as analogs. Every number on the site traces to a source file.

## Link to Project Demo

PENDING: the demo video link has not been supplied. If there is no video by submission, use the site address: https://gsoplatform.vercel.app

## Link to Final Project

https://gsoplatform.vercel.app

## Detailed Project Description

The challenge asks for Earth places that could stand in for candidate Moon-base locations or Mars landing and exploration sites, and for an honest account of what makes each place analogous and where the analogy breaks down. GSOP is a transparent, reproducible screening method for that search, with an India focus.

What it does. GSOP splits the land into equal-area tiles and gives each tile a similarity score against three targets: two lunar south pole sites (Connecting Ridge C1 and the Shackleton rim) and Jezero crater on Mars. The Moon score uses slope, illumination, roughness and relief. The Mars score uses sunlight, slope, relief and air density. A Monte Carlo of 2000 runs varies the weights. A tile is flagged when it stays in the top 5 percent of scores in at least 90 percent of runs. Flagged tiles are shown as candidates not in our reference list. We list 20 regions, at most the top 10 per target, and every one is marked Unreviewed. One lunar target has none, because its flagged groups of tiles are all too small.

What failed, shown first. The criteria were pre-registered before results were computed. The method failed its negative-control test: the Namib sand sea scored at percentile 90.2 and the Rub' al Khali at percentile 75.6, against a pre-registered maximum of percentile 25.0. On Mars, the median percentile of the primary sites was 61.3, below the pre-registered minimum of percentile 90.0, so Mars is a low-confidence secondary result. The Moon score also turned out to be terrain only: removing the illumination weight leaves the top group of tiles unchanged (overlap 1.0000). The site shows these results on its Failure-First Ledger and its Honest Map instead of hiding them.

Where the analogy breaks down. Gravity, air pressure, dust, radiation and regolith are not scored, and neither are temperature, rock composition and thermal inertia for the Moon. An Earth place can match a target's terrain and still differ in everything else that matters for a mission. The ledger lists these differences, most of them provisional, and every site page has a section on where its analogy breaks down.

India focus. We list the India sites in our reference set with the stored result at each, and say plainly that most have no score because land-cover or data gates removed them. Of the 20 regions we list, one overlaps the India outline: Region 04, with 94 tiles inside it. It is unreviewed, and the outline is a generalised shape, not an official map.

Making it checkable. Every number on the site has a row in a claims file that names its source file and hash. One command rebuilds every data file, and a second run gives identical output. A check on every change fails on banned wording, an unsourced number, or an altered uncertainty statement. The uncertainty statement from the analysis is printed word for word beside the results: "The Monte Carlo varies the weights and, for the Moon only, the slope and relief measurement error, and applies no systematic Earth bias to any of the 15 Earth columns, so the reported score bands and robust-tile counts understate the real uncertainty."

What it cannot tell you. The ranking has not been checked against independent data. It is a screening aid. If a region survives review, it is a place where a human look is worth starting, and it cannot replace that look.

## NASA Data

Used in the scores:
- SRTM elevation (CGIAR-CSI version), for Earth slope, relief and roughness.
- MODIS land cover (MCD12Q1) and vegetation index (MOD13A2), from NASA LP DAAC, to remove water, ice, vegetated and built or farmed tiles.
- LRO LOLA south polar elevation model and permanently shadowed region map, from the NASA Planetary Geodesy Data Archive, for the lunar targets.
- Mars Global Surveyor MOLA elevation, served by USGS Astrogeology, for the Mars target.

Used for context only, not scored:
- Mars Odyssey THEMIS-derived thermal inertia of Jezero (Edwards and Buz, on Zenodo), to set a target value.
- LRO Diviner south polar thermal product and Mars Global Surveyor TES thermal inertia maps, from the NASA Planetary Data System, as reference layers with their limits on the Methods page.
- NASA Mars fact sheet and NASA Glenn atmosphere models, for solar constants and air density.

## Space Agency Partner & Other Data

- ESA Copernicus DEM GLO30 (attribution to DLR and Airbus), for Earth elevation where SRTM does not reach.
- Natural Earth, public domain, for the India outline and region names (desert, plateau, range and populated place layers).
- Mars Climate Database, from the Laboratoire de Meteorologie Dynamique with ESA and CNES support, used only to set Jezero target values, not scored.
- Google Earth Engine, used to read the NASA and Copernicus layers.
- Published sources for target locations and limits: Barker et al. on the LOLA south pole model, and Glaser et al. on lighting at the lunar south pole.
- No partner agency endorses this project.

## Use of Artificial Intelligence

Yes. AI assistants were used, under human direction, and the site is built so that AI output cannot become a number on the site.
- The website, the data build scripts and the documentation were written with Claude Code, an AI coding assistant from Anthropic. Changes go through pull requests that must pass automated checks, and a person reviews the finished site and this text before submission.
- Parts of the earlier analysis and its decision log were written with AI assistants. Where the record says so, entries are marked as assistant-written, and evidence gathered by chat assistants is marked as not re-verified.
- The list of analog sites, and its descriptive text, came from a spreadsheet produced with an AI model. The site labels that text "teammate-written, unreviewed". The similarity scores in that spreadsheet are AI estimates and are never shown anywhere on the site.
- Every number shown comes from stored simulation results or from a source file, with a hash. No number is generated by an AI model at build time or in the browser.
