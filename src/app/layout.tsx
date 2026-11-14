import type { Metadata, Viewport } from "next";
import "./globals.css";
import ThemeProvider from "./components/ThemeProvider";

const title = "GSOP: Geospatial Similarity Observation Platform";
const description =
  "A transparent, reproducible screening method for Earth places that resemble lunar and Martian targets.";
const og = "/brand/og/gsop-og-image-1200x630.png";

const siteUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: title, template: "%s | GSOP" },
  description,
  manifest: "/brand/favicons/site.webmanifest",
  icons: {
    icon: [
      { url: "/brand/favicons/favicon.ico", sizes: "any" },
      { url: "/brand/favicons/favicon-dark.svg", type: "image/svg+xml", media: "(prefers-color-scheme: dark)" },
      { url: "/brand/favicons/favicon-light.svg", type: "image/svg+xml", media: "(prefers-color-scheme: light)" },
      { url: "/brand/favicons/favicon-dark-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/brand/favicons/favicon-dark-16x16.png", sizes: "16x16", type: "image/png" },
    ],
    apple: "/brand/favicons/apple-touch-icon.png",
    other: [{ rel: "mask-icon", url: "/brand/favicons/safari-pinned-tab.svg", color: "#06080A" }],
  },
  openGraph: {
    type: "website",
    siteName: "GSOP",
    title,
    description,
    images: [{ url: og, width: 1200, height: 630, alt: "The Moon, Earth and Mars" }],
  },
  twitter: { card: "summary_large_image", title, description, images: [og] },
};

export const viewport: Viewport = {
  colorScheme: "dark light",
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#06080A" },
    { media: "(prefers-color-scheme: light)", color: "#F4F5F3" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
