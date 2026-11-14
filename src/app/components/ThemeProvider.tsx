"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";

// Brand tokens key off data-theme. Dark is the default. The OS preference only
// applies once a visitor picks "System" in the toggle; next-themes then writes
// the resolved value (dark or light) to data-theme.
export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider attribute="data-theme" defaultTheme="dark" enableSystem themes={["dark", "light"]} disableTransitionOnChange>
      {children}
    </NextThemesProvider>
  );
}
