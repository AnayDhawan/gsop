import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { chipFor, claim, lookupFile, measurementsFile, sitesFile } from "@/lib/data";
import { claimIds, evidenceFor } from "@/lib/evidence";
import MeasuredEvidence from "./MeasuredEvidence";
import { statusLabel } from "@/lib/format";
import { viewName } from "@/lib/names";
import type { Site } from "@/lib/types";

export const dynamicParams = false;

export function generateStaticParams() {
  return [...new Set(sitesFile().sites.map((s) => s.slug))].map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const s = sitesFile().sites.find((x) => x.slug === slug);
  return { title: s ? s.name : "Site" };
}

const NONE = "not provided";

function Text({ label, value }: { label: string; value: string | null }) {
  return (
    <section className="space-y-1">
      <h3 className="text-lg">{label}</h3>
      <p className={value ? "" : "text-muted-foreground"}>{value && value.trim() ? value : NONE}</p>
    </section>
  );
}

function v1Line(s: Site): string {
  const id = s.v1_match.site_id.replace(/^[a-z_]+\//, "").replace(/_/g, " ");
  const km = claim(`sites.${s.id}.v1_match_km`);
  if (s.v1_used === true) return `Yes. This place matches the v1 site "${id}", about ${km} km away.`;
  if (s.v1_used === false) return `No. The nearest v1 site, "${id}", is about ${km} km away.`;
  return `Unknown. The nearest v1 site, "${id}", is about ${km} km away, and the files cannot say whether v1 meant the same place.`;
}

function SitePage({ s, withBody }: { s: Site; withBody: boolean }) {
  const lookup = lookupFile().sites[s.id] ?? {};
  const views = Object.keys(lookup);
  const lat = claim(`sites.${s.id}.lat`);
  const lon = claim(`sites.${s.id}.lon`);
  const elev = s.elevation_m !== null ? claim(`sites.${s.id}.elevation_m`) : null;
  const year = s.year_first_used_as_analog !== null ? claim(`sites.${s.id}.year_first_used_as_analog`) : null;
  const sources = [s.source_url_1, s.source_url_2, s.source_url_3].filter(Boolean) as string[];
  // Optional section (C8): only when the v2 evidence file exists. Without it the page is unchanged.
  const meas = measurementsFile();
  const siteRows = meas?.by_site[s.id] ?? [];
  const ids = claimIds(s.id, siteRows);
  const evidence = meas ? evidenceFor(siteRows, (m) => claim(ids.get(m) as string)) : null;
  return (
    <section className="space-y-8" aria-label={withBody ? `${s.name}, ${s.body}` : undefined}>
      {withBody && <h2 className="text-2xl">{s.body}</h2>}

      <div className="space-y-2 border border-border p-4">
        <p className="gsop-label">{s.status === "draft" ? "Unreviewed draft" : s.status}</p>
        <p>
          This page was built from a teammate-supplied list. The text is <strong>teammate-written, unreviewed</strong>.
          {s.sources_ok ? "" : " Sources pending."}
        </p>
        {s.list === "candidate" && <p>This is a candidate: a suggestion that is not in our reference list.</p>}
      </div>

      <Text label="Summary" value={s.summary} />

      <section className="space-y-1">
        <h3 className="text-lg">Location</h3>
        <dl className="grid gap-x-6 gap-y-1 text-sm md:grid-cols-[12rem_1fr]">
          <dt className="text-muted-foreground">Country</dt>
          <dd>{s.country ?? NONE}</dd>
          <dt className="text-muted-foreground">Coordinates</dt>
          <dd>
            {lat}, {lon}
            {s.coord_source === "csv_approx" ? " (approximate)" : ""}
          </dd>
          <dt className="text-muted-foreground">Elevation (m)</dt>
          <dd>{elev ?? NONE}</dd>
          <dt className="text-muted-foreground">Year first used as an analog</dt>
          <dd>{year ?? NONE}</dd>
        </dl>
      </section>

      <Text label="Terrain and geology" value={s.terrain_geology} />
      <Text label="Climate" value={s.climate} />
      <Text label="Parameters matched" value={s.parameters_matched} />
      <Text label="Why it is an analog" value={s.why_analog} />
      <Text label="Key differences: where the analogy breaks down" value={s.key_differences} />
      <Text label="Experiments done" value={s.experiments_done} />
      <Text label="Experiments proposed" value={s.experiments_possible} />
      <Text label="How to adjust it" value={s.how_to_modify} />
      <Text label="Access" value={s.access_and_facilities} />
      <Text label="Hazards" value={s.hazards} />

      <section className="space-y-1">
        <h3 className="text-lg">Sources</h3>
        {sources.length === 0 ? (
          <p className="text-muted-foreground">Sources pending ({s.source_note}).</p>
        ) : (
          <ul className="list-disc pl-6">
            {sources.map((u) => (
              <li key={u}>
                <a href={u} className="underline underline-offset-4">
                  {u}
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>

      <MeasuredEvidence evidence={evidence} chip={chipFor(s.slug)} radiusClaim={(r) => claim(`v2.evidence.radius.${r}`)} />

      <section className="space-y-3">
        <h3 className="text-lg">v1 score, percentile and overlap flag</h3>
        <p className="text-secondary-foreground">
          A descriptive lookup of scores v1 already stored. It is not a test, and a high percentile here does not show that this is a good analog.
        </p>
        <p>
          <span className="gsop-label">v1 used this site</span>
          <br />
          {v1Line(s)}
        </p>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <caption className="sr-only">Stored v1 scores near {s.name}</caption>
            <thead>
              <tr className="border-b border-border">
                <th scope="col" className="py-2 pr-4 font-medium">Score view</th>
                <th scope="col" className="py-2 pr-4 font-medium">Result</th>
                <th scope="col" className="py-2 pr-4 font-medium">Percentile</th>
                <th scope="col" className="py-2 pr-4 font-medium">Score</th>
                <th scope="col" className="py-2 pr-4 font-medium">Distance to tile (km)</th>
                <th scope="col" className="py-2 pr-4 font-medium">Overlap flag</th>
              </tr>
            </thead>
            <tbody>
              {views.map((v) => {
                const e = lookup[v];
                const ok = e.status === "scored";
                return (
                  <tr key={v} className="border-b border-border align-top">
                    <th scope="row" className="py-2 pr-4 font-medium">
                      {viewName(v)}
                    </th>
                    <td className="py-2 pr-4">
                      {ok ? "Scored" : statusLabel(e.status)}
                      {!ok && "reason" in e ? <span className="block text-xs text-muted-foreground">{e.reason}</span> : null}
                    </td>
                    <td className="py-2 pr-4">{ok ? claim(`lookup.${s.id}.${v}.percentile`) : NONE}</td>
                    <td className="py-2 pr-4">{ok ? claim(`lookup.${s.id}.${v}.score`) : NONE}</td>
                    <td className="py-2 pr-4">{ok ? claim(`lookup.${s.id}.${v}.km_to_tile`) : NONE}</td>
                    <td className="py-2 pr-4">{ok && e.status === "scored" ? (e.top5_in_90pct_runs ? "In a flagged tile" : "Not in a flagged tile") : NONE}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-sm text-muted-foreground">
          Overlap flag: whether the tile used for the score is one v1 flagged as stable in its top group across the Monte Carlo runs.
        </p>
        <details className="text-sm text-secondary-foreground">
          <summary className="cursor-pointer">What these scores can and cannot tell you</summary>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            {lookupFile().meta.limits.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </details>
      </section>
    </section>
  );
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const rows = sitesFile().sites.filter((x) => x.slug === slug).sort((a, b) => Number(a.body === "Mars") - Number(b.body === "Mars"));
  if (rows.length === 0) notFound();
  return (
    <article className="max-w-4xl space-y-8">
      <p className="text-sm">
        <Link href="/sites" className="underline underline-offset-4">
          All sites
        </Link>
      </p>
      <h1 className="text-3xl">{rows[0].name}</h1>
      {rows.length > 1 && rows.some((r) => r.name !== rows[0].name) && (
        <p className="text-sm text-secondary-foreground">The same place appears under both bodies, with its own text for each.</p>
      )}
      {rows.map((s) => (
        <SitePage key={s.id} s={s} withBody={rows.length > 1} />
      ))}
    </article>
  );
}
