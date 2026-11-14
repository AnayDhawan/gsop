"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { DEFAULT_VIEW, defaultFilters, filterRows, viewOptions, type ExplorerRow, type Filters } from "@/lib/explorer";
import { statusLabel } from "@/lib/format";

type Props = { rows: ExplorerRow[]; views: { Moon: string[]; Mars: string[] } };

const field = "border border-border bg-surface px-2 py-1 text-sm";

export default function Explorer({ rows, views }: Props) {
  const [f, setF] = useState<Filters>(defaultFilters());
  const set = (patch: Partial<Filters>) => setF((p) => ({ ...p, ...patch }));
  const shown = useMemo(() => filterRows(rows, f), [rows, f]);
  const options = viewOptions(views[f.body]);

  return (
    <div className="space-y-4">
      <form className="grid gap-4 md:grid-cols-3" onSubmit={(e) => e.preventDefault()} aria-label="Filter sites">
        <fieldset className="space-y-1">
          <legend className="gsop-label">Body</legend>
          <div className="flex gap-4">
            {(["Moon", "Mars"] as const).map((b) => (
              <label key={b} className="flex items-center gap-1 text-sm">
                <input type="radio" name="body" checked={f.body === b} onChange={() => set({ body: b, view: DEFAULT_VIEW[b] })} />
                {b}
              </label>
            ))}
          </div>
        </fieldset>
        <label className="space-y-1 text-sm">
          <span className="gsop-label block">Score shown</span>
          <select className={field + " w-full"} value={f.view} onChange={(e) => set({ view: e.target.value })}>
            {options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="gsop-label block">Search name or country</span>
          <input className={field + " w-full"} type="search" value={f.q} onChange={(e) => set({ q: e.target.value })} />
        </label>
        <label className="space-y-1 text-sm">
          <span className="gsop-label block">Entry type</span>
          <select className={field + " w-full"} value={f.list} onChange={(e) => set({ list: e.target.value as Filters["list"] })}>
            <option value="all">All entries</option>
            <option value="known">Reference sites</option>
            <option value="candidate">Candidates</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="gsop-label block">v1 used this site</span>
          <select className={field + " w-full"} value={f.v1} onChange={(e) => set({ v1: e.target.value as Filters["v1"] })}>
            <option value="all">Any</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="unknown">Unknown</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="gsop-label block">Result</span>
          <select className={field + " w-full"} value={f.result} onChange={(e) => set({ result: e.target.value as Filters["result"] })}>
            <option value="all">Scored and unscored</option>
            <option value="scored">Scored only</option>
            <option value="unscored">Unscored only</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="gsop-label block">Sort</span>
          <select className={field + " w-full"} value={f.sort} onChange={(e) => set({ sort: e.target.value as Filters["sort"] })}>
            <option value="name">Name</option>
            <option value="pct_desc">Percentile, high to low</option>
            <option value="pct_asc">Percentile, low to high</option>
          </select>
        </label>
        <label className="flex items-center gap-2 self-end pb-1 text-sm">
          <input type="checkbox" checked={f.flaggedOnly} onChange={(e) => set({ flaggedOnly: e.target.checked })} />
          Only tiles flagged in the top group
        </label>
        <div className="self-end pb-1">
          <button type="button" className="gsop-label border border-border px-3 py-1 hover:text-foreground" onClick={() => setF(defaultFilters())}>
            Reset filters
          </button>
        </div>
      </form>

      <div role="status" aria-live="polite" className="min-h-6 text-sm text-secondary-foreground">
        {shown.length === 0 ? "No sites match these filters." : ""}
      </div>

      {shown.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <caption className="sr-only">Sites with the stored v1 score at each</caption>
            <thead>
              <tr className="border-b border-border">
                <th scope="col" className="py-2 pr-4 font-medium">Site</th>
                <th scope="col" className="py-2 pr-4 font-medium">Entry type</th>
                <th scope="col" className="py-2 pr-4 font-medium">Country</th>
                <th scope="col" className="py-2 pr-4 font-medium">v1 used this site</th>
                <th scope="col" className="py-2 pr-4 font-medium">Result</th>
                <th scope="col" className="py-2 pr-4 font-medium">Percentile</th>
                <th scope="col" className="py-2 pr-4 font-medium">Score</th>
                <th scope="col" className="py-2 pr-4 font-medium">Top-group flag</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => {
                const c = r.cells[f.view];
                const scored = c?.status === "scored";
                return (
                  <tr key={r.id} className="border-b border-border align-top">
                    <th scope="row" className="py-2 pr-4 font-medium">
                      <Link href={`/sites/${r.slug}`} className="underline underline-offset-4">
                        {r.name}
                      </Link>
                    </th>
                    <td className="py-2 pr-4">{r.list === "known" ? "Reference site" : "Candidate"}</td>
                    <td className="py-2 pr-4">{r.country ?? "not provided"}</td>
                    <td className="py-2 pr-4">{r.v1_used === true ? "Yes" : r.v1_used === false ? "No" : "Unknown"}</td>
                    <td className="py-2 pr-4">
                      {scored ? "Scored" : statusLabel(c?.status ?? "not in v1 outputs")}
                      {!scored && c?.reason ? <span className="block text-xs text-muted-foreground">{c.reason}</span> : null}
                    </td>
                    <td className="py-2 pr-4">{scored ? c.percentile : "-"}</td>
                    <td className="py-2 pr-4">{scored ? c.score : "-"}</td>
                    <td className="py-2 pr-4">{scored ? (c.flagged ? "Flagged" : "Not flagged") : "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
