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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
              <Key size={16} className="text-indigo-600" />
            </div>
            <div>
              <h2 className="text-slate-900 font-semibold text-sm">Enter your API key</h2>
              <p className="text-slate-500 text-xs mt-0.5">Required to access the gateway</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          <div className="relative">
            <input
              type={show ? "text" : "password"}
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSave()}
              placeholder="gw-••••••••••••••••••••••••••••••••"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 pr-10 text-slate-900 text-sm font-mono placeholder-slate-400 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all"
              autoFocus
            />
            <button
              onClick={() => setShow(!show)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
            >
              {show ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Your key is stored only in your browser (localStorage) and never sent to any server other than the gateway.
          </p>
        </div>

        {/* Footer */}
        <div className="px-6 pb-5 flex gap-2">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!value.trim() || saved}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
          >
            {saved ? (
              <><CheckCircle2 size={15} className="text-emerald-300" /> Saved!</>
            ) : (
              "Save Key"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
