import Image from "next/image";
import Link from "next/link";
import SiteNav from "./SiteNav";
import ThemeToggle from "./ThemeToggle";

export default function SiteHeader() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-3 px-6 py-4">
        <Link href="/" aria-label="GSOP home" className="shrink-0">
          <Image className="gsop-logo gsop-logo--dark" src="/brand/logos/gsop-logo-horizontal-dark.svg" alt="GSOP: Geospatial Similarity Observation Platform" width={200} height={38} priority unoptimized />
          <Image className="gsop-logo gsop-logo--light" src="/brand/logos/gsop-logo-horizontal-light.svg" alt="" aria-hidden width={200} height={38} priority unoptimized />
        </Link>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <SiteNav />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
