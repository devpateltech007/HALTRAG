import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";

export const metadata: Metadata = {
  title: "HALT-RAG · Trust-Aware Retrieval-Augmented Generation",
  description:
    "Detect, classify, and localize hallucinations in high-stakes AI answers."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen">
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <Topbar />
            <main className="flex-1 p-6 lg:p-10 max-w-[1400px] w-full mx-auto">
              {children}
            </main>
            <footer className="px-6 lg:px-10 py-6 text-xs text-white/40 text-center">
              HALT-RAG · Trust-Aware RAG · Graduate Research Demo
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
