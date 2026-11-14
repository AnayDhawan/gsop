import type { Metadata } from "next";
import { lookupFile } from "@/lib/data";
import { explorerData } from "@/lib/explorer-data";
import Explorer from "./Explorer";

export const metadata: Metadata = { title: "Sites" };

export default function Page() {
  const { rows, views } = explorerData();
  const lookup = lookupFile();
  return (
    <div className="space-y-6">
      <header className="max-w-3xl space-y-3">
        <h1 className="text-3xl">Sites</h1>
        <ul className="list-disc space-y-1 pl-6 text-secondary-foreground">
          <li>Search and filter the reference sites by body and entry type. Each name opens that site&apos;s page.</li>
          <li>Reference sites are places named as analogs in a teammate-supplied list. Candidates are suggestions that are not in our reference list.</li>
          <li>The numbers are stored v1 scores, looked up at each site. This is a descriptive lookup, not a test, and the ranking has not been checked against independent data.</li>
          <li>All site text is teammate-written and unreviewed. No sources have been checked yet.</li>
        </ul>
        <details className="text-sm text-secondary-foreground">
          <summary className="cursor-pointer">What the scores can and cannot tell you</summary>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            {lookup.meta.limits.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </details>
      </header>
      <Explorer rows={rows} views={views} />
    </div>
  );
}
