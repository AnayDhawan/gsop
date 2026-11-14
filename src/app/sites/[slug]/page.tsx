import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { sitesFile } from "@/lib/data";

export const dynamicParams = false;

export function generateStaticParams() {
  return [...new Set(sitesFile().sites.map((s) => s.slug))].map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const s = sitesFile().sites.find((x) => x.slug === slug);
  return { title: s ? s.name : "Site" };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const rows = sitesFile().sites.filter((x) => x.slug === slug);
  if (rows.length === 0) notFound();
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">{rows[0].name}</h1>
      <p className="text-secondary-foreground">This page is under construction.</p>
    </div>
  );
}
