"use client";
import { useState } from "react";
import { Key, X, Eye, EyeOff, CheckCircle2 } from "lucide-react";
import { setApiKey } from "@/lib/api";

interface KeySetupModalProps {
  onClose: () => void;
}

export default function KeySetupModal({ onClose }: KeySetupModalProps) {
  const [value, setValue] = useState("");
  const [show, setShow] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    if (!value.trim()) return;
    setApiKey(value.trim());
    setSaved(true);
    setTimeout(() => onClose(), 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#18181b] rounded-xl shadow-2xl border border-white/[0.1] w-full max-w-md mx-4 overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.07]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-500/15 border border-brand-500/20 flex items-center justify-center">
              <Key size={14} className="text-brand-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-[14px]">Enter your API key</h2>
              <p className="text-zinc-500 text-[12px] mt-0.5">Required to access the gateway</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.05] rounded-lg transition-colors">
            <X size={15} />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-3">
          <div className="relative">
            <input
              type={show ? "text" : "password"}
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSave()}
              placeholder="gw-••••••••••••••••••••••••••••••••"
              className="w-full bg-[#09090b] border border-white/[0.1] rounded-lg px-4 py-2.5 pr-10 text-zinc-200 text-[13px] font-mono placeholder-zinc-700 outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/30 transition-all"
              autoFocus
            />
            <button
              onClick={() => setShow(!show)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-300 transition-colors"
            >
              {show ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
          <p className="text-[12px] text-zinc-600 leading-relaxed">
            Stored only in your browser — never sent to any third party.
          </p>
        </div>

        {/* Footer */}
        <div className="px-5 pb-5 flex gap-2">
          <button onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-lg border border-white/[0.08] text-zinc-400 text-[13px] font-medium hover:bg-white/[0.04] transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!value.trim() || saved}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-[13px] font-medium transition-colors"
          >
            {saved ? (
              <><CheckCircle2 size={14} className="text-emerald-300" /> Saved!</>
            ) : "Save Key"}
          </button>
        </div>
      </div>
    </div>
  );
}
