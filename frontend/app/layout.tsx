import "../styles/globals.css";
import { ReactNode } from "react";
import NavConditional from "../components/NavConditional";
import LenisProvider from "../components/LenisProvider";

export const metadata = {
  title: "Void",
  description: "Grok style landing with Spline background, lenis, glass UI"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-black text-white antialiased">
        <LenisProvider>
          <div className="relative min-h-screen overflow-x-hidden">
            <NavConditional />
            <main className="pt-24">{children}</main>
          </div>
        </LenisProvider>
      </body>
    </html>
  );
}
