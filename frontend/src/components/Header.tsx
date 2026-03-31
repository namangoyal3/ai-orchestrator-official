"use client";
import Link from "next/link";
import { useState } from "react";
import { Bell, Settings, Key } from "lucide-react";
import KeySetupModal from "@/components/KeySetupModal";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [showKeyModal, setShowKeyModal] = useState(false);

  return (
    <>
      <header className="h-16 border-b border-slate-200 bg-white/80 backdrop-blur-sm flex items-center justify-between px-6 sticky top-0 z-30">
        <div>
          <h2 className="text-slate-900 font-semibold text-lg">{title}</h2>
          {subtitle && <p className="text-slate-500 text-xs">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2">
          <Link href="/analytics" title="View analytics"
            className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors">
            <Bell size={18} />
          </Link>
          <button
            onClick={() => setShowKeyModal(true)}
            title="Configure API key"
            className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Key size={18} />
          </button>
          <Link href="/api-keys" title="Settings"
            className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors">
            <Settings size={18} />
          </Link>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
            D
          </div>
        </div>
      </header>

      {showKeyModal && <KeySetupModal onClose={() => setShowKeyModal(false)} />}
    </>
  );
}
