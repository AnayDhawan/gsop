"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

const OPTIONS = [
  { value: "dark", label: "Dark" },
  { value: "light", label: "Light" },
  { value: "system", label: "System" },
] as const;

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  // The stored choice is only known in the browser, so render no pressed state on the server or first paint.
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  return (
    <div role="group" aria-label="Colour theme" className="flex border border-border">
      {OPTIONS.map((o) => {
        const pressed = mounted && theme === o.value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={pressed}
            onClick={() => setTheme(o.value)}
            className={cn(
              "gsop-label px-2 py-1 text-xs",
              pressed ? "bg-surface-raised text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
