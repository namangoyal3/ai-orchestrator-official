"use client";
import Link from "next/link";
import { Bell, Settings } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm flex items-center justify-between px-6 sticky top-0 z-30">
      <div>
        <h2 className="text-white font-semibold text-lg">{title}</h2>
        {subtitle && <p className="text-slate-400 text-xs">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        <Link href="/analytics" title="View analytics"
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
          <Bell size={18} />
        </Link>
        <Link href="/api-keys" title="Manage API keys"
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
          <Settings size={18} />
        </Link>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
          D
        </div>
      </div>
    </header>
  );
}
