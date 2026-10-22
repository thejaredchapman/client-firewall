import type { Metadata } from "next";
import copy from "@/content/copy.json";
import "./globals.css";

export const metadata: Metadata = { title: copy.title, description: copy.tagline };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
