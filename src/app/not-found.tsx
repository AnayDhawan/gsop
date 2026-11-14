import Link from "next/link";

export default function NotFound() {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Page not found</h1>
      <p className="text-secondary-foreground">
        That address does not match a page on this site. <Link href="/" className="underline underline-offset-4">Back to the home page</Link>.
      </p>
    </div>
  );
}
