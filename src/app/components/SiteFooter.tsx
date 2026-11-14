import Link from "next/link";
import { NAV, REPO_URL } from "@/lib/nav";

export default function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-border">
      <div className="mx-auto grid w-full max-w-6xl gap-8 px-6 py-8 text-sm text-secondary-foreground md:grid-cols-3">
        <div className="space-y-2">
          <p className="gsop-label">About</p>
          <p>GSOP is an independent research prototype built for the NASA Space Apps Challenge. It is not an official NASA tool.</p>
          <p>The ranking is a screening aid. It has not been checked against independent data. The limits are on the ledger page.</p>
        </div>
        <div className="space-y-2">
          <p className="gsop-label">Pages</p>
          <ul className="space-y-1">
            {NAV.map((n) => (
              <li key={n.href}>
                <Link href={n.href} className="hover:text-foreground">
                  {n.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-2">
          <p className="gsop-label">Open source</p>
          <p>
            Code and data build are on{" "}
            <a href={REPO_URL} className="underline underline-offset-4 hover:text-foreground">
              GitHub
            </a>
            , under the MIT licence.
          </p>
          <p>
            Open data credits are on the{" "}
            <Link href="/credits" className="underline underline-offset-4 hover:text-foreground">
              data credits page
            </Link>
            .
          </p>
        </div>
      </div>
    </footer>
  );
}
