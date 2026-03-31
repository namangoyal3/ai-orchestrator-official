import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "AI Gateway — Universal LLM Orchestration",
  description: "Route any task to the optimal LLM, agent, or tool. Built for developers who need reliable AI infrastructure.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-[#09090b] text-zinc-100 antialiased">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-[240px] min-h-screen bg-[#09090b]">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
