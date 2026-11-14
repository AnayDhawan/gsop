import Link from "next/link";
import { claim, e32Sentence, headline, lookupFile, regionsFile, sitesFile } from "@/lib/data";
import { statusLabel } from "@/lib/format";
import { targetName } from "@/lib/names";

const link = "underline underline-offset-4";

export default function Home() {
  const h = headline();
  const lookup = lookupFile();
  const regions = regionsFile().regions;
  const inIndia = regions.filter((r) => r.n_tiles_in_india > 0);
  const indiaSites = sitesFile().sites.filter((s) => s.list === "known" && (s.country ?? "").startsWith("India"));
  const baseView = (body: string) => (body === "Moon" ? "shackleton_rim__base" : "jezero__base");

  return (
    <div className="space-y-14">
      <section className="max-w-3xl space-y-5">
        <h1 className="text-3xl md:text-4xl">{h.headline}</h1>
        <p className="text-lg text-secondary-foreground">{h.support}</p>
        <p className="flex flex-wrap gap-x-6 gap-y-2">
          <Link href="/ledger" className={`font-display text-lg ${link}`}>
            Start with what failed
          </Link>
          <Link href="/map" className={`font-display text-lg ${link}`}>
            Open the Honest Map
          </Link>
          <Link href="/sites" className={`font-display text-lg ${link}`}>
            Browse the sites
          </Link>
        </p>
      </section>

      <section className="max-w-3xl space-y-3" aria-labelledby="what">
        <h2 id="what" className="text-2xl">
          What this is
        </h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>A screening method. It scores every land tile on Earth by how closely its terrain matches a lunar or Martian target, then ranks the tiles.</li>
          <li>Transparent and reproducible. The data files are built by one command from stored results, and every number on this site traces to a source file.</li>
          <li>It has an India focus: below, the India sites we list and where the flagged regions fall.</li>
          <li>Flagged tiles and regions are candidates not in our reference list. They are unreviewed.</li>
        </ul>
      </section>

      <section className="max-w-3xl space-y-4" aria-labelledby="failed">
        <h2 id="failed" className="text-2xl">
          What failed
        </h2>
        <ul className="space-y-3">
          <li className="border border-control p-4">
            The negative-control test failed on the Moon run. Two places that should score low scored high: the Namib sand sea at percentile {claim("metrics.moon.control.namib_sand_sea.rank_pct")} and the Rub&apos; al Khali at percentile{" "}
            {claim("metrics.moon.control.rub_al_khali.rank_pct")}. The pre-registered maximum was percentile {claim("metrics.moon.criterion.negative_control_rank_pct_max")}.
          </li>
          <li className="border border-control p-4">
            On the Mars run, the median percentile of the primary sites was {claim("metrics.mars.primary_median_rank_pct")}, below the pre-registered minimum of percentile{" "}
            {claim("metrics.mars.criterion.primary_median_rank_pct_min")}. Mars is a low-confidence secondary result.
          </li>
          <li className="border border-border p-4">
            The Moon score is effectively terrain only. Removing the illumination weight leaves the top group of tiles unchanged (overlap {claim("metrics.terrain_only.shackleton_rim__base.overlap_without_illumination")}).
          </li>
        </ul>
        <p className="text-secondary-foreground">
          The ranking has not been checked against independent data. The full list of failures and of where the analogy breaks down is on the{" "}
          <Link href="/ledger" className={link}>
            Failure-First Ledger
          </Link>
          .
        </p>
        <blockquote className="border-l-2 border-border pl-4">{e32Sentence()}</blockquote>
      </section>

      <section className="max-w-3xl space-y-4" aria-labelledby="india">
        <h2 id="india" className="text-2xl">
          India focus
        </h2>
        <p className="text-secondary-foreground">
          Sites in our list that are in India, with the stored v1 result at each. A descriptive lookup, not a test. A site with no score says nothing about how good an analog it is.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <caption className="sr-only">Reference sites in India</caption>
            <thead>
              <tr className="border-b border-border">
                <th scope="col" className="py-2 pr-4 font-medium">Site</th>
                <th scope="col" className="py-2 pr-4 font-medium">Listed for</th>
                <th scope="col" className="py-2 pr-4 font-medium">Score shown</th>
                <th scope="col" className="py-2 pr-4 font-medium">Result</th>
              </tr>
            </thead>
            <tbody>
              {indiaSites.map((s) => {
                const view = baseView(s.body);
                const e = lookup.sites[s.id]?.[view];
                return (
                  <tr key={s.id} className="border-b border-border align-top">
                    <th scope="row" className="py-2 pr-4 font-medium">
                      <Link href={`/sites/${s.slug}`} className={link}>
                        {s.name}
                      </Link>
                    </th>
                    <td className="py-2 pr-4">{s.body}</td>
                    <td className="py-2 pr-4">{targetName(view.split("__")[0])}, base</td>
                    <td className="py-2 pr-4">
                      {e?.status === "scored" ? `Percentile ${claim(`lookup.${s.id}.${view}.percentile`)}` : e ? `${statusLabel(e.status)}: ${e.reason}` : "not in v1 outputs"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p>
          {inIndia.length === 0 ? (
            "None of the regions we list overlaps the India outline."
          ) : (
            <>
              Of the {claim("regions.count")} regions we list, {inIndia.length === 1 ? "one overlaps" : "some overlap"} the India outline used by v1:{" "}
              {inIndia.map((r, i) => (
                <span key={r.id}>
                  {i > 0 ? ", " : ""}
                  {r.id} ({claim(`regions.${r.id.replace(" ", "_")}.n_tiles_in_india`)} tiles)
                </span>
              ))}
              . The outline is a generalised Natural Earth shape, not an official map. Regions are unreviewed.
            </>
          )}{" "}
          See them on the{" "}
          <Link href="/map" className={link}>
            Honest Map
          </Link>
          .
        </p>
      </section>

      <section className="max-w-3xl space-y-3" aria-labelledby="next">
        <h2 id="next" className="text-2xl">
          Read next
        </h2>
        <ul className="list-disc space-y-1 pl-6">
          <li>
            <Link href="/method" className={link}>
              Method
            </Link>
            : what the screening does and does not do.
          </li>
          <li>
            <Link href="/credits" className={link}>
              Data credits
            </Link>
            : the open data behind the scores.
          </li>
        </ul>
      </section>
    </div>
  );
}
