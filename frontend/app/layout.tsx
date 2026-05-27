import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Marriott AI Concierge",
  description: "Find the perfect Marriott hotel with AI-powered search",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-900 antialiased h-screen overflow-hidden">
        {children}
      </body>
    </html>
  );
}
