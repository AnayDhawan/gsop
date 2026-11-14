"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";

// Brand tokens key off data-theme. Dark is the default; the OS preference only
// applies once a visitor picks "system" in the toggle (issue C1).
export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider attribute="data-theme" defaultTheme="dark" themes={["dark", "light"]}>
      {children}
    </NextThemesProvider>
  );
}
