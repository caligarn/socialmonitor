import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";

export const metadata: Metadata = {
  title: "SocialMonitor",
  description:
    "Monitor trends, track AI influencers, and plan AI-generated content",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen">
        <Nav />
        <main className="flex-1 overflow-y-auto p-6 lg:p-10">{children}</main>
      </body>
    </html>
  );
}
