import Link from "next/link";
import { NAV } from "@/lib/nav";
import { headline } from "@/lib/data";

export default function Home() {
  const h = headline();
  return (
    <div className="space-y-8">
      <h1 className="text-3xl md:text-4xl">{h.headline}</h1>
      <p className="max-w-2xl text-lg text-secondary-foreground">{h.support}</p>
      <ul className="grid gap-4 md:grid-cols-2">
        {NAV.map((n) => (
          <li key={n.href} className="border border-border p-4">
            <Link href={n.href} className="font-display text-lg underline underline-offset-4">
              {n.label}
            </Link>
            <p className="text-sm text-secondary-foreground">{n.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
