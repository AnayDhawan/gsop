import type { Metadata } from "next";
import Link from "next/link";
import { claim, e32Sentence } from "@/lib/data";

export const metadata: Metadata = { title: "Method" };

export default function Page() {
  const runs = claim("metrics.view.shackleton_rim__base.runs");
  const p5 = claim("method.top_fraction_five_pct");
  const p90 = claim("method.min_run_share_pct");
  return (
    <article className="max-w-3xl space-y-8">
      <h1 className="text-3xl">Method</h1>

      <section className="space-y-3">
        <h2 className="text-xl">What the screening does</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>It splits the land into equal-area tiles and gives each tile a similarity score to one lunar or Martian target.</li>
          <li>Moon targets are Connecting Ridge C1 and the Shackleton rim at the south pole. The Mars target is Jezero.</li>
          <li>The Moon score uses slope, illumination, roughness and relief. The Mars score uses sunlight, slope, relief and air density.</li>
          <li>
            A Monte Carlo of {runs} runs varies the weights. A tile is flagged when it is in the top {p5}% of scores in at least {p90}% of runs.
          </li>
          <li>The results are a lookup of stored v1 values. Nothing on this site recomputes a score.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl">What it cannot tell you</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>The Moon score is effectively terrain only. The illumination family adds nothing to the Moon ranking.</li>
          <li>Mars is a low-confidence secondary result.</li>
          <li>Gravity, air pressure, dust, radiation, regolith, temperature and rock composition are not scored.</li>
          <li>v1 failed its negative controls, and the ranking has not been checked against independent data.</li>
          <li>
            Flagged tiles are candidates not in our reference list. They are unreviewed. The{" "}
            <Link href="/ledger" className="underline underline-offset-4">
              Failure-First Ledger
            </Link>{" "}
            lists what failed and where the analogy breaks down.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl">Uncertainty</h2>
        <blockquote className="border-l-2 border-border pl-4 text-secondary-foreground">{e32Sentence()}</blockquote>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl">How the data were built</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>One build command turns the stored v1 results into the data files this site reads.</li>
          <li>Every number on a page has a row in a claims file that names its source file and hash.</li>
          <li>A check runs on every change and fails on banned wording, an unsourced number, or an altered uncertainty sentence.</li>
        </ul>
      </section>
    </article>
  );
}
