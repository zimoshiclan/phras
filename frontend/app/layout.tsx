import "./globals.css";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Phras — your linguistic fingerprint",
  description: "Upload text, get a Style ID, make any AI sound like you.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="max-w-6xl mx-auto px-6">
          <nav className="flex items-center gap-6 py-5 border-b border-neutral-800 mb-10">
            <Link href="/" className="font-bold text-lg tracking-tight">Phras</Link>
            <div className="flex gap-5 text-sm text-neutral-400">
              <Link href="/dashboard" className="hover:text-neutral-100 transition-colors">Dashboard</Link>
              <Link href="/playground" className="hover:text-neutral-100 transition-colors">Playground</Link>
              <Link href="/docs" className="hover:text-neutral-100 transition-colors">Docs</Link>
            </div>
          </nav>
          <div className="pb-16">{children}</div>
        </div>
      </body>
    </html>
  );
}
