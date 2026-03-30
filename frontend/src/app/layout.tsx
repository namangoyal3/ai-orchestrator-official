import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "AI Gateway Orchestrator",
  description: "Universal AI infrastructure — automatically routes to the best LLM, agents, and tools for any task.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-[260px] min-h-screen bg-slate-950">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
