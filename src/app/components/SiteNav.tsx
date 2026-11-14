"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV, isActive } from "@/lib/nav";
import { cn } from "@/lib/utils";

export default function SiteNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="flex flex-wrap gap-x-5 gap-y-1">
      {NAV.map((n) => {
        const active = isActive(pathname, n.href);
        return (
          <Link
            key={n.href}
            href={n.href}
            aria-current={active ? "page" : undefined}
            className={cn("text-sm", active ? "text-foreground underline underline-offset-4" : "text-secondary-foreground hover:text-foreground")}
          >
            {n.label}
          </Link>
        );
      })}
    </nav>
  );
}
