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
      <header className="h-14 border-b border-white/[0.07] bg-[#09090b]/80 backdrop-blur-sm flex items-center justify-between px-6 sticky top-0 z-30">
        <div>
          <h2 className="text-white font-semibold text-[15px] leading-tight">{title}</h2>
          {subtitle && <p className="text-zinc-500 text-[12px] mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-1">
          <Link href="/analytics" title="View analytics"
            className="p-2 text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.05] rounded-lg transition-colors">
            <Bell size={16} />
          </Link>
          <button
            onClick={() => setShowKeyModal(true)}
            title="Configure API key"
            className="p-2 text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.05] rounded-lg transition-colors"
          >
            <Key size={16} />
          </button>
          <Link href="/api-keys" title="Settings"
            className="p-2 text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.05] rounded-lg transition-colors">
            <Settings size={16} />
          </Link>
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white text-[11px] font-bold ml-1">
            A
          </div>
        </div>
      </header>

      {showKeyModal && <KeySetupModal onClose={() => setShowKeyModal(false)} />}
    </>
  );
}
