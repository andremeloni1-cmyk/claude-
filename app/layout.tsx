import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Andre Meloni — Business Dashboard",
  description: "Jobs and financials dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} h-full antialiased`}>
      <body className="h-full bg-gray-50 text-gray-900">
        <Navigation />
        <main className="ml-56 min-h-screen p-8">{children}</main>
      </body>
    </html>
  );
}
