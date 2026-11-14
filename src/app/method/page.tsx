import type { Metadata } from "next";
import Link from "next/link";
import { claim, e32Sentence, v2File } from "@/lib/data";
import LimitsDoc from "./LimitsDoc";

export const metadata: Metadata = { title: "Methods and limits" };

const link = "underline underline-offset-4";
const ul = "list-disc space-y-2 pl-6";
const h2 = "text-2xl";

export default function Page() {
  const v2 = v2File();
  const doc = (id: string) => v2.limits_docs.find((d) => d.id === id);
  const refs = doc("refs_limits");
  const runs = claim("metrics.view.shackleton_rim__base.runs");
  const p5 = claim("method.top_fraction_five_pct");
  const p90 = claim("method.min_run_share_pct");
  const area = claim("regions.tile_area_km2");
  const radius = claim("lookup.match_radius_km");
  const minTiles = claim("regions.min_tiles");
  const dropKm = claim("regions.drop_distance_km");
  const topN = claim("regions.top_n");
  const nearKm = claim("regions.near_km");
  const terrainShare = claim("metrics.earth.share_land_tiles_with_terrain");
  const unconfirmed = claim("ledger.moon.unconfirmed_sites");
  const maxControl = claim("metrics.moon.criterion.negative_control_rank_pct_max");
  const minMedian = claim("metrics.mars.criterion.primary_median_rank_pct_min");
  const namib = claim("metrics.moon.control.namib_sand_sea.rank_pct");
  const rub = claim("metrics.moon.control.rub_al_khali.rank_pct");
  const marsMedian = claim("metrics.mars.primary_median_rank_pct");
  const illumWeight = claim("metrics.terrain_only.shackleton_rim__base.illumination_weight");
  const illumMax = claim("metrics.terrain_only.shackleton_rim__base.illum_match_max");

  return (
    <article className="max-w-3xl space-y-12">
      <header className="space-y-4">
        <h1 className="text-3xl">Methods and limits</h1>
        <ul className={ul}>
          <li>GSOP scores every land tile on Earth by how closely its terrain matches a lunar or Martian target, then ranks the tiles.</li>
          <li>It is a screening method. It says where to look, not where to go.</li>
          <li>The Moon score is effectively terrain only. Mars is a low-confidence secondary result.</li>
          <li>
            The method failed its own pre-registered negative-control test. The{" "}
            <Link href="/ledger" className={link}>
              Failure-First Ledger
            </Link>{" "}
            lists every failure first, and so does this page.
          </li>
          <li>The ranking has not been checked against independent data.</li>
        </ul>
      </header>

      <section className="space-y-3" aria-labelledby="question">
        <h2 id="question" className={h2}>
          The question
        </h2>
        <ul className={ul}>
          <li>
            The challenge asks for Earth places that could serve as analogs for candidate Moon-base locations or Mars landing and exploration sites. It also asks what makes a place analogous, where the analogy breaks down, and how studying it could help.
          </li>
          <li>GSOP answers one narrow part: which Earth places have terrain like a lunar or Martian target, using open data. It does not say what to test at a place.</li>
          <li>An analog is useful only for the properties that match. The properties that do not match are on the ledger and in the limits below.</li>
        </ul>
      </section>

      <section className="space-y-3" aria-labelledby="limits">
        <h2 id="limits" className={h2}>
          Limits
        </h2>
        <h3 className="text-lg">What the score cannot see</h3>
        <ul className={ul}>
          <li>
            The Moon score is effectively terrain only. The illumination family was given a weight of {illumWeight}, but the highest lighting match on any Earth tile is {illumMax}, so it changes nothing.
          </li>
          <li>Gravity, air pressure, dust, radiation and regolith are not scored. Neither are temperature, rock composition and thermal inertia for the Moon, or water, dust and temperature for Mars.</li>
          <li>An Earth place can match a target&apos;s terrain and still differ in everything else that matters for a mission. The ledger lists those differences, most of them provisional.</li>
        </ul>
        <h3 className="text-lg">Data limits</h3>
        <ul className={ul}>
          <li>Only tiles that passed the land-cover and data gates have a score. Water and ice, vegetated tiles, built or farmed tiles and tiles without data are left out, so large regions never appear.</li>
          <li>Terrain data exist for a share of {terrainShare} of land tiles. Tiles without terrain data are never scored. The coverage report names tiles beyond the reach of the main elevation dataset as part of the gap but does not explain all of it.</li>
          <li>Earth slope is not corrected for the map projection, so it reads too steep toward the equator and too gentle toward the poles. A latitude band check was run to see whether the ranking holds.</li>
          <li>Terrain data change source at the northern edge of the main elevation dataset, and roughness steps up across that seam.</li>
          <li>The coordinates of {unconfirmed} of the sites v1 used are not confirmed from a primary source.</li>
        </ul>
        <h3 className="text-lg">Result limits</h3>
        <ul className={ul}>
          <li>
            Two negative controls scored high on the Moon run: the Namib sand sea at percentile {namib} and the Rub&apos; al Khali at percentile {rub}, against a pre-registered maximum of percentile {maxControl}.
          </li>
          <li>
            On the Mars run the median percentile of the primary sites was {marsMedian}, below the pre-registered minimum of percentile {minMedian}. The Moon primary-site criterion could not be tested.
          </li>
          <li>The score bands come from varying the weights and not the Earth data, so they understate the real uncertainty. The uncertainty section below prints the full statement.</li>
          <li>Everything from v1 is provisional.</li>
        </ul>
        <h3 className="text-lg">Site and region limits</h3>
        <ul className={ul}>
          <li>Reference sites come from a teammate-supplied list. Their text is teammate-written and unreviewed, and no source has been checked yet.</li>
          <li>Regions and tiles are candidates not in our reference list. They are unreviewed.</li>
          <li>
            Region names are labels from Natural Earth, which is generalised: the desert, plateau or range the centre lies in, one whose outline is within {nearKm} km, or else the nearest populated place. A name is not a claim about the ground.
          </li>
        </ul>
      </section>

      <section className="space-y-3" aria-labelledby="works">
        <h2 id="works" className={h2}>
          How the screening works
        </h2>
        <ol className="list-decimal space-y-2 pl-6">
          <li>
            <strong>Tiles.</strong> Land is split into equal-area tiles of {area} square kilometres each.
          </li>
          <li>
            <strong>Gates.</strong> Tiles that are water or ice, vegetated, built or farmed, or that lack data are removed.
          </li>
          <li>
            <strong>Targets.</strong> The Moon targets are Connecting Ridge C1 and the Shackleton rim at the south pole. The Mars target is Jezero.
          </li>
          <li>
            <strong>Features.</strong> The Moon score uses slope, illumination, roughness and relief. The Mars score uses sunlight, slope, relief and air density.
          </li>
          <li>
            <strong>Score.</strong> Each tile gets a similarity to the target, where higher means more similar. Three purpose profiles weight the features differently: base, landing and mobility, and power and night.
          </li>
          <li>
            <strong>Monte Carlo.</strong> {runs} runs vary the weights. For the Moon they also vary the slope and relief measurement error.
          </li>
          <li>
            <strong>Flag.</strong> A tile is flagged when it is in the top {p5}% of scores in at least {p90}% of runs. This measures stability to the weights, not whether the ranking is right.
          </li>
          <li>
            <strong>Sites.</strong> A site gets the score of the best-scoring scored tile within {radius} km. Its percentile is the share of scored tiles in that view with a lower score. This is a lookup of stored values, not a test.
          </li>
          <li>
            <strong>Regions.</strong> Neighbouring flagged tiles are joined. Groups under {minTiles} tiles and groups within {dropKm} km of a reference site are dropped. Each target lists its top {topN} regions by median score.
          </li>
          <li>
            <strong>This site.</strong> Pages read stored results. Nothing here recomputes a score, and every number traces to a source file and hash.
          </li>
        </ol>
      </section>

      <section className="space-y-3" aria-labelledby="checks">
        <h2 id="checks" className={h2}>
          Checks fixed before the run
        </h2>
        <ul className={ul}>
          <li>Before results were computed, v1 fixed three criteria: the primary sites must rank high, the negative controls must rank low, and obviously unsuitable ground must be rejected by the gates.</li>
          <li>Pre-registration hashes are on the ledger. A hash identifies the plan. It does not mean the plan was met.</li>
          <li>
            Result: the controls failed, the Moon primary criterion could not be tested, the Mars primary criterion failed, and the gate tests passed. See the{" "}
            <Link href="/ledger" className={link}>
              ledger
            </Link>{" "}
            for the numbers and what each means for the analogy.
          </li>
        </ul>
      </section>

      <section className="space-y-3" aria-labelledby="what">
        <h2 id="what" className={h2}>
          What each score uses
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <caption className="sr-only">Features used and not used, by body</caption>
            <thead>
              <tr className="border-b border-border">
                <th scope="col" className="py-2 pr-4 font-medium">Body</th>
                <th scope="col" className="py-2 pr-4 font-medium">Used in the score</th>
                <th scope="col" className="py-2 pr-4 font-medium">Not scored</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-border align-top">
                <th scope="row" className="py-2 pr-4 font-medium">Moon</th>
                <td className="py-2 pr-4">Slope, illumination (no effect), roughness, relief</td>
                <td className="py-2 pr-4">Water or ice, composition, temperature, thermal inertia</td>
              </tr>
              <tr className="border-b border-border align-top">
                <th scope="row" className="py-2 pr-4 font-medium">Mars (low confidence)</th>
                <td className="py-2 pr-4">Sunlight, slope, relief, air density</td>
                <td className="py-2 pr-4">Roughness, composition, water, dust, temperature, thermal inertia</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3" aria-labelledby="v2">
        <h2 id="v2" className={h2}>
          The v2 limits
        </h2>
        <p className={v2.run_completed ? "" : "text-control"}>{v2.status_text}</p>
        {refs ? (
          <>
            <p className="text-secondary-foreground">
              The reference thermal layers give context for the Moon and Mars targets. This is where each layer cannot match Earth, as written with the data.
            </p>
            <details className="border border-border p-4" open>
              <summary className="cursor-pointer font-display text-lg">{refs.title}</summary>
              <div className="mt-3">
                <LimitsDoc blocks={refs.blocks} />
              </div>
            </details>
          </>
        ) : (
          <p className="text-muted-foreground">The thermal reference limits are not available.</p>
        )}
        {(["evidence_limits", "data_resources"] as const).map((id) => {
          const d = doc(id);
          return d ? (
            <details key={id} className="border border-border p-4" open>
              <summary className="cursor-pointer font-display text-lg">{d.title}</summary>
              <div className="mt-3">
                <LimitsDoc blocks={d.blocks} />
              </div>
            </details>
          ) : (
            <p key={id} className="text-muted-foreground">
              {id === "evidence_limits" ? "Site evidence limits: not available yet. The evidence run has not produced them." : "Data resource table: not available yet."}
            </p>
          );
        })}
      </section>

      <section className="space-y-3" aria-labelledby="uncertainty">
        <h2 id="uncertainty" className={h2}>
          Uncertainty
        </h2>
        <blockquote className="border-l-2 border-border pl-4">{e32Sentence()}</blockquote>
      </section>

      <section className="space-y-3" aria-labelledby="data">
        <h2 id="data" className={h2}>
          Data and reproducibility
        </h2>
        <ul className={ul}>
          <li>One build command turns the stored results into the data files this site reads. A second run gives identical files.</li>
          <li>Every number on a page has a row in a claims file that names its source file and hash. A check on every change fails on banned wording, an unsourced number or an altered uncertainty sentence.</li>
          <li>
            The open data behind the scores are on the{" "}
            <Link href="/credits" className={link}>
              data credits page
            </Link>
            .
          </li>
          <li>Anything v1 did not store reads &quot;not in v1 outputs&quot;. Nothing is estimated.</li>
        </ul>
      </section>

      <section className="space-y-3" aria-labelledby="glossary">
        <h2 id="glossary" className={h2}>
          Glossary
        </h2>
        <dl className="space-y-2">
          {[
            ["Tile", "One equal-area cell of the Earth grid. Each gets at most one score per target."],
            ["Gate", "A rule that removes a tile before scoring: water or ice, vegetation, built or farmed land, or missing data."],
            ["Percentile", "The share of scored tiles in a view with a lower score than this one."],
            ["Flag", "A tile that stays in the top group across most Monte Carlo runs. It measures stability, not correctness."],
            ["Negative control", "A place that should score low. A high score means the ranking cannot tell it from a good match."],
            ["Pre-registration", "A written plan of the criteria, fixed before results were computed."],
            ["Reference site", "A place named as an analog in our list. It is not a scored result."],
            ["Candidate", "A tile, region or suggested place that is not in our reference list. Unreviewed."],
            ["Provisional", "Not yet checked by us. Most ledger entries are provisional."],
          ].map(([term, def]) => (
            <div key={term}>
              <dt className="font-medium">{term}</dt>
              <dd className="text-secondary-foreground">{def}</dd>
            </div>
          ))}
        </dl>
      </section>
    </article>
  );
}
