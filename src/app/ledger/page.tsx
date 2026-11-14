import type { Metadata } from "next";
import Link from "next/link";
import { e32Sentence, ledgerFile, metricsFile } from "@/lib/data";
import { shortHash, sourceName, statusLabel } from "@/lib/format";
import { viewName } from "@/lib/names";
import type { LedgerEntry, Metric } from "@/lib/types";

export const metadata: Metadata = { title: "Failure-First Ledger" };

const RUNS = [
  { id: "moon", label: "Moon" },
  { id: "moon_lat20-40", label: "Moon, latitude band check" },
  { id: "mars", label: "Mars (low confidence)" },
];
const CRITERIA = [
  { key: "primary_median_ge_min", label: "Primary site median" },
  { key: "controls_below_max", label: "Negative controls" },
  { key: "gate_tests_all_rejected", label: "Gate tests" },
];
const CONTROLS = [
  { id: "namib_sand_sea", label: "Namib sand sea" },
  { id: "rub_al_khali", label: "Rub' al Khali" },
  { id: "amazon_basin", label: "Amazon basin" },
  { id: "congo_basin", label: "Congo basin" },
];

function Source({ file, sha }: { file: string; sha: string }) {
  return (
    <p className="gsop-mono text-xs text-muted-foreground">
      Source: {sourceName(file)} ({shortHash(sha)})
    </p>
  );
}

function Entry({ e, failed = false }: { e: LedgerEntry; failed?: boolean }) {
  return (
    <li className={`space-y-2 border p-4 ${failed ? "border-control" : "border-border"}`}>
      <p>{e.statement}</p>
      <p className="text-secondary-foreground">
        <span className="gsop-label">What this means for the analogy</span>
        <br />
        {e.what_this_means_for_the_analogy}
      </p>
      <p className="gsop-label">
        {statusLabel(e.status)}
        {e.provisional ? " | Provisional" : ""}
      </p>
      <Source file={e.source_file} sha={e.sha256} />
    </li>
  );
}

export default function Page() {
  const ledger = ledgerFile();
  const metrics = metricsFile().metrics;
  const byId = new Map<string, Metric>(metrics.map((m) => [m.id, m]));
  const m = (id: string): Metric => {
    const v = byId.get(id);
    if (!v) throw new Error(`metrics.json has no ${id}`);
    return v;
  };
  const of = (type: LedgerEntry["type"]) => ledger.entries.filter((e) => e.type === type);
  const failedControls = of("failed_control");
  const limits = of("known_limit");
  const terrainOnly = limits.filter((e) => e.id === "known_limit.moon_terrain_only");
  const otherLimits = limits.filter((e) => e.id !== "known_limit.moon_terrain_only");
  const unscored = of("unscored_property");
  const physical = of("physical_difference");
  const hashes = ledger.meta.preregistration_hashes as Record<string, string>;

  return (
    <div className="max-w-4xl space-y-12">
      <header className="space-y-4">
        <h1 className="text-3xl">Failure-First Ledger</h1>
        <ul className="list-disc space-y-1 pl-6 text-secondary-foreground">
          <li>This page lists what failed, then where the analogy breaks down. It comes before any results on purpose.</li>
          <li>v1 is an earlier analysis whose criteria were fixed before it ran. Several criteria failed or could not be tested.</li>
          <li>Nothing here is a success claim. The ranking has not been checked against independent data.</li>
        </ul>
        <blockquote className="border-l-2 border-border pl-4">{e32Sentence()}</blockquote>
      </header>

      <section className="space-y-4" aria-labelledby="failed">
        <h2 id="failed" className="text-2xl">
          What failed
        </h2>
        <ul className="space-y-4">
          {failedControls.map((e) => (
            <Entry key={e.id} e={e} failed />
          ))}
        </ul>

        <h3 className="text-lg">Pre-registered criteria, by run</h3>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 pr-4 font-medium">Run</th>
                {CRITERIA.map((c) => (
                  <th key={c.key} className="py-2 pr-4 font-medium">
                    {c.label}
                  </th>
                ))}
                <th className="py-2 pr-4 font-medium">All criteria passed</th>
              </tr>
            </thead>
            <tbody>
              {RUNS.map((r) => (
                <tr key={r.id} className="border-b border-border align-top">
                  <th scope="row" className="py-2 pr-4 font-medium">
                    {r.label}
                  </th>
                  {CRITERIA.map((c) => {
                    const v = m(`${r.id}.status.${c.key}`).display;
                    return (
                      <td key={c.key} className={`py-2 pr-4 ${v === "fail" ? "text-control" : ""}`}>
                        {statusLabel(v)}
                      </td>
                    );
                  })}
                  <td className="py-2 pr-4">{statusLabel(m(`${r.id}.all_criteria_passed`).display)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Source file={m("moon.status.controls_below_max").source_file} sha={m("moon.status.controls_below_max").sha256} />

        <h3 className="text-lg">Negative controls</h3>
        <p className="text-secondary-foreground">
          Controls are places that should score low. Scores are percentiles among scored tiles. The pre-registered maximum was percentile{" "}
          {m("moon.criterion.negative_control_rank_pct_max").display}.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 pr-4 font-medium">Control</th>
                <th className="py-2 pr-4 font-medium">Moon run</th>
                <th className="py-2 pr-4 font-medium">Mars run</th>
              </tr>
            </thead>
            <tbody>
              {CONTROLS.map((c) => {
                const moonScore = byId.get(`moon.control.${c.id}.rank_pct`);
                const moonStatus = byId.get(`moon.control.${c.id}.status`);
                const marsStatus = byId.get(`mars.control.${c.id}.status`);
                return (
                  <tr key={c.id} className="border-b border-border">
                    <th scope="row" className="py-2 pr-4 font-medium">
                      {c.label}
                    </th>
                    <td className={`py-2 pr-4 ${moonScore ? "text-control" : ""}`}>
                      {moonScore ? `Percentile ${moonScore.display}` : moonStatus ? statusLabel(moonStatus.display) : "Not run"}
                    </td>
                    <td className="py-2 pr-4">{marsStatus ? statusLabel(marsStatus.display) : "Not run"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-secondary-foreground">
          Mars primary site median: percentile {m("mars.primary_median_rank_pct").display}, against a pre-registered minimum of percentile{" "}
          {m("mars.criterion.primary_median_rank_pct_min").display}.
        </p>
        <Source file={m("moon.control.namib_sand_sea.rank_pct").source_file} sha={m("moon.control.namib_sand_sea.rank_pct").sha256} />
      </section>

      <section className="space-y-4" aria-labelledby="terrain">
        <h2 id="terrain" className="text-2xl">
          The Moon score is terrain only
        </h2>
        <ul className="space-y-4">
          {terrainOnly.map((e) => (
            <Entry key={e.id} e={e} />
          ))}
        </ul>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 pr-4 font-medium">Moon view</th>
                <th className="py-2 pr-4 font-medium">Illumination weight</th>
                <th className="py-2 pr-4 font-medium">Highest lighting match on any tile</th>
                <th className="py-2 pr-4 font-medium">Overlap without illumination</th>
              </tr>
            </thead>
            <tbody>
              {metrics
                .filter((x) => x.id.startsWith("terrain_only.") && x.id.endsWith(".illumination_weight"))
                .map((w) => {
                  const view = w.id.split(".")[1];
                  return (
                    <tr key={view} className="border-b border-border">
                      <th scope="row" className="py-2 pr-4 font-medium">
                        {viewName(view)}
                      </th>
                      <td className="py-2 pr-4">{w.display}</td>
                      <td className="py-2 pr-4">{m(`terrain_only.${view}.illum_match_max`).display}</td>
                      <td className="py-2 pr-4">{m(`terrain_only.${view}.overlap_without_illumination`).display}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="breaks">
        <h2 id="breaks" className="text-2xl">
          Where the analogy breaks down
        </h2>
        <p className="text-secondary-foreground">
          These physical differences come from the v1 limits ledger. Most entries are provisional and have not been verified by us.
        </p>
        <ul className="space-y-4">
          {physical.map((e) => (
            <Entry key={e.id} e={e} />
          ))}
        </ul>
      </section>

      <section className="space-y-4" aria-labelledby="unscored">
        <h2 id="unscored" className="text-2xl">
          What is not scored
        </h2>
        {(["moon", "mars"] as const).map((b) => (
          <div key={b} className="space-y-3">
            <h3 className="text-lg">{b === "moon" ? "Moon" : "Mars"}</h3>
            <ul className="space-y-4">
              {unscored
                .filter((e) => e.body === b)
                .map((e) => (
                  <Entry key={e.id} e={e} />
                ))}
            </ul>
          </div>
        ))}
      </section>

      <section className="space-y-4" aria-labelledby="other">
        <h2 id="other" className="text-2xl">
          Other known limits
        </h2>
        <ul className="space-y-4">
          {otherLimits.map((e) => (
            <Entry key={e.id} e={e} />
          ))}
        </ul>
      </section>

      <section className="space-y-3" aria-labelledby="prereg">
        <h2 id="prereg" className="text-2xl">
          Pre-registration
        </h2>
        <p className="text-secondary-foreground">
          The criteria were written down before results were computed. The hash identifies that record. It does not mean the test was passed.
        </p>
        <ul className="space-y-1">
          {Object.entries(hashes).map(([run, h]) => (
            <li key={run} className="gsop-mono break-all text-xs">
              {run}: {h}
            </li>
          ))}
        </ul>
        <p>
          See the{" "}
          <Link href="/method" className="underline underline-offset-4">
            method page
          </Link>{" "}
          for what the screening does.
        </p>
      </section>
    </div>
  );
}
