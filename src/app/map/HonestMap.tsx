"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";
import { DEFAULT_TOGGLES, KIND_LABEL, KIND_ORDER, itemKey, project, visibleItems, type ItemKind, type MapItem, type MapTarget, type Toggles } from "@/lib/map";
import { cn } from "@/lib/utils";

const ZOOMS = [1, 2, 4];

function Marker({ item, target, selected, onSelect }: { item: MapItem; target: MapTarget; selected: boolean; onSelect: () => void }) {
  const { x, y } = project(item.lat, item.lon, target.bounds);
  const aria = `${KIND_LABEL[item.kind]}: ${item.label}`;
  if (item.kind === "region" && item.bbox) {
    const a = project(item.bbox.north, item.bbox.west, target.bounds);
    const b = project(item.bbox.south, item.bbox.east, target.bounds);
    if (b.x > a.x) {
      return (
        <button
          type="button"
          aria-label={aria}
          title={aria}
          onClick={onSelect}
          className={cn("absolute border-2 border-positive bg-positive/10", selected && "bg-positive/40")}
          style={{ left: `${a.x}%`, top: `${a.y}%`, width: `${b.x - a.x}%`, height: `${b.y - a.y}%`, minWidth: 10, minHeight: 10 }}
        />
      );
    }
  }
  const base = "absolute -translate-x-1/2 -translate-y-1/2";
  const look: Record<ItemKind, string> = {
    site: "h-3 w-3 rounded-full border border-background bg-earth",
    candidate: "h-3 w-3 rounded-full border-2 border-earth bg-transparent",
    control: "h-4 w-4 rotate-45 border-2 border-foreground bg-control",
    region: "h-3 w-3 border-2 border-positive",
    tile: "h-1.5 w-1.5 rounded-full bg-foreground ring-1 ring-background",
  };
  return (
    <button
      type="button"
      aria-label={aria}
      title={aria}
      onClick={onSelect}
      className={cn(base, look[item.kind], selected && "outline outline-2 outline-offset-2 outline-ring")}
      style={{ left: `${x}%`, top: `${y}%` }}
    />
  );
}

export default function HonestMap({ targets, sentence, controlMax }: { targets: MapTarget[]; sentence: string; controlMax: string }) {
  const [targetId, setTargetId] = useState(targets.find((t) => t.target === "shackleton_rim")?.target ?? targets[0].target);
  const [toggles, setToggles] = useState<Toggles>(DEFAULT_TOGGLES);
  const [zoom, setZoom] = useState(0);
  const [mode, setMode] = useState<"map" | "table">("map");
  const [selected, setSelected] = useState<string | null>(null);
  const target = targets.find((t) => t.target === targetId)!;
  const shown = useMemo(() => visibleItems(target.items, toggles), [target, toggles]);
  const sel = shown.find((i) => itemKey(i) === selected) ?? null;
  const present = KIND_ORDER.filter((k) => target.items.some((i) => i.kind === k));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-x-8 gap-y-3">
        <fieldset className="space-y-1">
          <legend className="gsop-label">Score overlay</legend>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {targets.map((t) => (
              <label key={t.target} className="flex items-center gap-1 text-sm">
                <input type="radio" name="overlay" checked={t.target === targetId} onChange={() => (setTargetId(t.target), setSelected(null))} />
                {t.name} ({t.body}
                {t.confidence === "low" ? ", low confidence" : ""})
              </label>
            ))}
          </div>
        </fieldset>
        <fieldset className="space-y-1">
          <legend className="gsop-label">Show</legend>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {present.map((k) => (
              <label key={k} className={cn("flex items-center gap-1 text-sm", k === "control" && "text-control")}>
                <input type="checkbox" checked={toggles[k]} onChange={(e) => setToggles({ ...toggles, [k]: e.target.checked })} />
                {KIND_LABEL[k]}
                {k === "control" || k === "tile" ? "s" : k === "region" ? "s" : k === "site" ? "s" : "s"}
              </label>
            ))}
          </div>
        </fieldset>
        <div role="group" aria-label="View" className="flex self-end border border-border">
          {(["map", "table"] as const).map((m) => (
            <button key={m} type="button" aria-pressed={mode === m} onClick={() => setMode(m)} className={cn("gsop-label px-3 py-1", mode === m ? "bg-surface-raised text-foreground" : "hover:text-foreground")}>
              {m === "map" ? "Map" : "Table"}
            </button>
          ))}
        </div>
      </div>

      {mode === "map" ? (
        <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
          <div className="space-y-2">
            <div className="flex gap-2">
              <button type="button" className="gsop-label border border-border px-2 py-1 disabled:opacity-40" onClick={() => setZoom(Math.min(zoom + 1, ZOOMS.length - 1))} disabled={zoom === ZOOMS.length - 1}>
                Zoom in
              </button>
              <button type="button" className="gsop-label border border-border px-2 py-1 disabled:opacity-40" onClick={() => setZoom(Math.max(zoom - 1, 0))} disabled={zoom === 0}>
                Zoom out
              </button>
              <button type="button" className="gsop-label border border-border px-2 py-1 disabled:opacity-40" onClick={() => setZoom(0)} disabled={zoom === 0}>
                Fit
              </button>
            </div>
            <div className="max-h-[75vh] overflow-auto border border-border bg-surface" tabIndex={0} role="region" aria-label={`Map of ${target.name} scores. Scroll to pan.`}>
              <div className="relative" style={{ width: `${ZOOMS[zoom] * 100}%`, aspectRatio: `${target.width} / ${target.height}` }}>
                <Image src={target.image} alt={`Score overlay for ${target.name}. Coloured land has a v1 score; transparent has none.`} width={target.width} height={target.height} unoptimized className="absolute inset-0 h-full w-full" priority />
                <svg className="pointer-events-none absolute inset-0 h-full w-full" preserveAspectRatio="none" viewBox="0 0 100 100" aria-hidden>
                  {[-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150].map((lon) => {
                    const x = project(0, lon, target.bounds).x;
                    return <line key={`lo${lon}`} x1={x} x2={x} y1={0} y2={100} stroke="currentColor" strokeOpacity={lon === 0 ? 0.5 : 0.2} strokeWidth={1} vectorEffect="non-scaling-stroke" />;
                  })}
                  {[-60, -30, 0, 30, 60].map((lat) => {
                    const y = project(lat, 0, target.bounds).y;
                    return y >= 0 && y <= 100 ? <line key={`la${lat}`} x1={0} x2={100} y1={y} y2={y} stroke="currentColor" strokeOpacity={lat === 0 ? 0.5 : 0.2} strokeWidth={1} vectorEffect="non-scaling-stroke" /> : null;
                  })}
                </svg>
                <span className="gsop-label pointer-events-none absolute left-1 text-[10px]" style={{ top: `${project(0, 0, target.bounds).y}%` }}>
                  Equator
                </span>
                <span className="gsop-label pointer-events-none absolute top-1 text-[10px]" style={{ left: `${project(0, 0, target.bounds).x + 0.3}%` }}>
                  Prime meridian
                </span>
                {shown.map((i) => (
                  <Marker key={itemKey(i)} item={i} target={target} selected={itemKey(i) === selected} onSelect={() => setSelected(itemKey(i))} />
                ))}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">Graticule lines are every thirty degrees. No coastline is drawn: the coloured land is the only context, and it shows only where v1 produced a score.</p>
          </div>

          <aside className="space-y-4" aria-label="Details and legend">
            <div role="status" aria-live="polite" className="space-y-2 border border-border p-3 text-sm">
              {sel ? (
                <>
                  <p className={cn("gsop-label", sel.kind === "control" && "text-control")}>{KIND_LABEL[sel.kind]}</p>
                  <p className="font-display text-lg">{sel.label}</p>
                  <p className="text-muted-foreground">
                    {sel.latText}, {sel.lonText}
                  </p>
                  <dl className="space-y-1">
                    {sel.details.map(([k, v]) => (
                      <div key={k}>
                        <dt className="gsop-label">{k}</dt>
                        <dd className={cn(sel.failed && (k === "Result" || k === "Verdict") && "text-control")}>{v}</dd>
                      </div>
                    ))}
                  </dl>
                  {sel.href && (
                    <Link href={sel.href} className="underline underline-offset-4">
                      Open the site page
                    </Link>
                  )}
                </>
              ) : (
                <p className="text-secondary-foreground">Select a marker to see its details.</p>
              )}
            </div>
            <div className="space-y-2 text-sm">
              <p className="gsop-label">Score colours</p>
              <Image src="/data/overlays/legend.png" alt="Colour scale from a low score (dark purple) to a high score (yellow)" width={512} height={64} unoptimized className="h-auto w-full" />
              <p className="text-xs text-muted-foreground">Transparent means v1 has no score there. It does not mean a low score.</p>
            </div>
            <ul className="space-y-1 text-xs text-secondary-foreground">
              <li>
                <span className="mr-2 inline-block h-2.5 w-2.5 rotate-45 border border-foreground bg-control align-middle" />
                <span className="text-control">Negative control</span>: should score low
              </li>
              <li>
                <span className="mr-2 inline-block h-3 w-3 rounded-full bg-earth align-middle" />
                Reference site
              </li>
              <li>
                <span className="mr-2 inline-block h-3 w-3 rounded-full border-2 border-earth align-middle" />
                Candidate, not in our reference list
              </li>
              <li>
                <span className="mr-2 inline-block h-3 w-3 border-2 border-positive align-middle" />
                Region, unreviewed
              </li>
              <li>
                <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-foreground align-middle" />
                Top tile
              </li>
            </ul>
          </aside>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <caption className="sr-only">Items on the map for {target.name}</caption>
            <thead>
              <tr className="border-b border-border">
                <th scope="col" className="py-2 pr-4 font-medium">Type</th>
                <th scope="col" className="py-2 pr-4 font-medium">Name</th>
                <th scope="col" className="py-2 pr-4 font-medium">Latitude</th>
                <th scope="col" className="py-2 pr-4 font-medium">Longitude</th>
                <th scope="col" className="py-2 pr-4 font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((i) => (
                <tr key={itemKey(i)} className="border-b border-border align-top">
                  <td className={cn("py-2 pr-4", i.failed && "text-control")}>{KIND_LABEL[i.kind]}</td>
                  <th scope="row" className="py-2 pr-4 font-medium">
                    {i.href ? (
                      <Link href={i.href} className="underline underline-offset-4">
                        {i.label}
                      </Link>
                    ) : (
                      i.label
                    )}
                  </th>
                  <td className="py-2 pr-4">{i.latText}</td>
                  <td className="py-2 pr-4">{i.lonText}</td>
                  <td className={cn("py-2 pr-4", i.failed && "text-control")}>
                    {i.details
                      .filter(([k]) => ["Result", "Percentile", "Score", "Place", "Median score", "Flagged in the top group"].includes(k))
                      .map(([k, v]) => `${k}: ${v}`)
                      .join("; ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <details className="text-sm text-secondary-foreground">
        <summary className="cursor-pointer">What this map can and cannot tell you</summary>
        <ul className="mt-2 list-disc space-y-1 pl-6">
          {target.limits.map((l) => (
            <li key={l}>{l}</li>
          ))}
          <li>Negative controls above the pre-registered maximum of percentile {controlMax} mean the ranking failed that test. See the Failure-First Ledger.</li>
        </ul>
      </details>
      <blockquote className="border-l-2 border-border pl-4 text-sm">{sentence}</blockquote>
    </div>
  );
}
