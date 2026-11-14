import type { Metadata } from "next";

export const metadata: Metadata = { title: "Data credits" };

const GROUPS: { title: string; items: string[] }[] = [
  {
    title: "Earth",
    items: [
      "Elevation: SRTM (CGIAR-CSI version) and the Copernicus DEM GLO30 beyond its coverage (attribution to DLR and Airbus).",
      "Land cover and vegetation gates: MODIS MCD12Q1 and MOD13A2 (NASA LP DAAC), read through Google Earth Engine.",
      "Air density: the NASA Glenn atmosphere model.",
      "India outline for labels: Natural Earth, public domain. It is not an official map.",
    ],
  },
  {
    title: "Moon",
    items: [
      "LOLA south-polar elevation and permanently shadowed region maps (NASA PGDA; Barker et al., Planetary Science Journal).",
      "Lighting and shadow statistics for the two targets: Glaser et al.",
    ],
  },
  {
    title: "Mars",
    items: [
      "MOLA elevation (USGS Astrogeology).",
      "Jezero thermal inertia and the Mars Climate Database: used to set target values, not scored.",
      "Solar constants and atmosphere: NASA Mars fact sheet and NASA Glenn Mars model. Jezero location: Grant et al.",
    ],
  },
];

export default function Page() {
  return (
    <article className="max-w-3xl space-y-8">
      <h1 className="text-3xl">Data credits</h1>
      <p className="text-secondary-foreground">
        This site uses open data. Licence wording is taken from the v1 provenance record and is still to be checked against each catalogue page.
      </p>
      {GROUPS.map((g) => (
        <section key={g.title} className="space-y-3">
          <h2 className="text-xl">{g.title}</h2>
          <ul className="list-disc space-y-2 pl-6">
            {g.items.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        </section>
      ))}
    </article>
  );
}
