import Image from "next/image";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-6 px-6 py-16">
      <Image
        className="gsop-logo gsop-logo--dark"
        src="/brand/logos/gsop-logo-horizontal-dark.svg"
        alt="GSOP: Geospatial Similarity Observation Platform"
        width={400}
        height={77}
        priority
        unoptimized
      />
      <Image
        className="gsop-logo gsop-logo--light"
        src="/brand/logos/gsop-logo-horizontal-light.svg"
        alt=""
        aria-hidden
        width={400}
        height={77}
        priority
        unoptimized
      />
      <p className="text-secondary-foreground">
        Placeholder page. Nav, theme toggle, footer and routes land in issue C1; the headline is locked in A6.
      </p>
    </main>
  );
}
