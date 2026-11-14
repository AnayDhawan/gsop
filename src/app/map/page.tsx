import type { Metadata } from "next";

export const metadata: Metadata = { title: "Honest Map" };

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Honest Map</h1>
      <p className="text-secondary-foreground">This page is under construction.</p>
    </div>
  );
}
