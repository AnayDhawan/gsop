import type { Metadata } from "next";
import Link from "next/link";
import { e32Sentence } from "@/lib/data";
import { mapData } from "@/lib/map-data";
import HonestMap from "./HonestMap";

export const metadata: Metadata = { title: "Honest Map" };

export default function Page() {
  const { targets, controlMax } = mapData();
  return (
    <div className="space-y-6">
      <header className="max-w-3xl space-y-3">
        <h1 className="text-3xl">Honest Map</h1>
        <ul className="list-disc space-y-1 pl-6 text-secondary-foreground">
          <li>The colours show where v1 produced a similarity score for one lunar or Martian target. Switch targets with the overlay control.</li>
          <li>Negative controls are shown in red. They are places that should score low, and two of them scored high. Read the{" "}
            <Link href="/ledger" className="underline underline-offset-4">
              Failure-First Ledger
            </Link>{" "}
            first.
          </li>
          <li>Regions and tiles are candidates not in our reference list. They are unreviewed.</li>
          <li>The Moon score is effectively terrain only. Mars is a low-confidence secondary result. The ranking has not been checked against independent data.</li>
        </ul>
      </header>
      <HonestMap targets={targets} sentence={e32Sentence()} controlMax={controlMax} />
    </div>
  );
}
