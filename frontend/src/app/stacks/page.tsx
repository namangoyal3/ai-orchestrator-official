"use client";
import { useState, useEffect } from "react";
import Header from "@/components/Header";
import { API_BASE, getApiKey } from "@/lib/api";
import {
  Globe, Database, Zap, Mail, CreditCard, Cloud, Shield,
  Brain, Package, Search, Radio, Clock, DollarSign,
  CheckCircle, ExternalLink, Copy, Check,
} from "lucide-react";

interface Tool {
  slug: string;
  name: string;
  description: string;
  tier: string;
  monthly_cost_usd: number;
  category: string;
}

interface Category {
  name: string;
  tools: Tool[];
}

interface StacksResponse {
  categories: Record<string, Tool[]>;
}

const CATEGORY_META: Record<string, { icon: React.ComponentType<{ size?: number; className?: string }>; color: string; label: string }> = {
  web:           { icon: Globe,       color: "text-blue-400",    label: "Web Frameworks" },
  database:      { icon: Database,    color: "text-emerald-400", label: "Databases" },
  cache:         { icon: Zap,         color: "text-yellow-400",  label: "Caching" },
  queue:         { icon: Radio,       color: "text-orange-400",  label: "Queues & Messaging" },
  auth:          { icon: Shield,      color: "text-purple-400",  label: "Authentication" },
  payments:      { icon: CreditCard,  color: "text-green-400",   label: "Payments" },
  email:         { icon: Mail,        color: "text-sky-400",     label: "Email" },
  notifications: { icon: Radio,       color: "text-pink-400",    label: "Notifications" },
  deploy:        { icon: Cloud,       color: "text-cyan-400",    label: "Deployment & Infra" },
  ai:            { icon: Brain,       color: "text-violet-400",  label: "AI & LLMs" },
  storage:       { icon: Package,     color: "text-indigo-400",  label: "Storage" },
  monitoring:    { icon: Clock,       color: "text-red-400",     label: "Monitoring" },
  search:        { icon: Search,      color: "text-amber-400",   label: "Search" },
  realtime:      { icon: Radio,       color: "text-teal-400",    label: "Realtime" },
};

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };
  return (
    <button onClick={handleCopy}
      className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.06] transition-colors">
      {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
    </button>
  );
}

function ToolCard({ tool }: { tool: Tool }) {
  const isFree = tool.monthly_cost_usd === 0;
  return (
    <div className="flex items-start gap-3 p-3.5 rounded-lg bg-white/[0.03] border border-white/[0.07] hover:border-white/[0.12] hover:bg-white/[0.05] transition-all group cursor-default">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[13px] font-medium text-white">{tool.name}</span>
          {isFree ? (
            <span className="badge badge-green text-[10px]">Free</span>
          ) : (
            <span className="badge badge-amber text-[10px]">${tool.monthly_cost_usd}/mo</span>
          )}
        </div>
        <p className="text-[12px] text-zinc-500 leading-relaxed line-clamp-2">{tool.description}</p>
      </div>
      {isFree && <CheckCircle size={14} className="text-emerald-400/60 shrink-0 mt-0.5" />}
    </div>
  );
}

export default function StacksPage() {
  const [data, setData] = useState<StacksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "free">("all");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const key = getApiKey();
    if (!key) { setLoading(false); setError("no-key"); return; }
    fetch(`${API_BASE}/v1/stacks`, { headers: { "X-API-Key": key } })
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => setError("fetch-error"))
      .finally(() => setLoading(false));
  }, []);

  const installCmd = "pip install namango && namango init";

  const handleCopyInstall = async () => {
    await navigator.clipboard.writeText(installCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const categories: Category[] = data
    ? Object.entries(data.categories).map(([name, tools]) => ({ name, tools }))
    : [];

  const filtered = activeFilter === "free"
    ? categories.map(c => ({ ...c, tools: c.tools.filter(t => t.monthly_cost_usd === 0) })).filter(c => c.tools.length > 0)
    : categories;

  const totalTools = categories.reduce((sum, c) => sum + c.tools.length, 0);
  const freeTools = categories.reduce((sum, c) => sum + c.tools.filter(t => t.monthly_cost_usd === 0).length, 0);

  return (
    <div className="min-h-screen">
      <Header title="Stacks" subtitle="Curated product-building tool catalog" />

      <div className="p-6 max-w-6xl mx-auto">

        {/* Hero banner */}
        <div className="relative mb-8 rounded-xl border border-brand-500/20 bg-brand-500/[0.05] overflow-hidden">
          <div className="absolute inset-0 bg-grid-dark bg-[size:24px_24px] opacity-40" />
          <div className="relative px-6 py-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex-1">
              <h2 className="text-white font-semibold text-base mb-1">
                Install the Namango CLI
              </h2>
              <p className="text-zinc-400 text-[13px]">
                Run <code className="text-brand-300 bg-brand-500/10 px-1.5 py-0.5 rounded text-[12px] font-mono">namango init</code> in your project — the CLI reads this catalog and recommends the right tools for your product.
              </p>
            </div>
            <div className="flex items-center gap-2 bg-[#09090b] border border-white/[0.1] rounded-lg px-4 py-2.5 font-mono text-[13px] text-zinc-300 shrink-0">
              <span className="text-zinc-600 select-none">$</span>
              <span>{installCmd}</span>
              <button onClick={handleCopyInstall}
                className="ml-2 p-1 text-zinc-500 hover:text-zinc-200 transition-colors">
                {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
              </button>
            </div>
          </div>
        </div>

        {/* Stats + filter */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div className="flex items-center gap-4 text-[13px]">
            <span className="text-zinc-400">
              <span className="text-white font-semibold">{totalTools}</span> tools across{" "}
              <span className="text-white font-semibold">{categories.length}</span> categories
            </span>
            <span className="text-zinc-600">·</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <DollarSign size={12} />
              <span className="font-medium">{freeTools} free</span>
            </span>
          </div>
          <div className="flex items-center gap-1 bg-white/[0.04] border border-white/[0.07] rounded-lg p-1">
            {(["all", "free"] as const).map(f => (
              <button key={f} onClick={() => setActiveFilter(f)}
                className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-all ${
                  activeFilter === f
                    ? "bg-white/[0.08] text-white"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}>
                {f === "all" ? "All tools" : "Free only"}
              </button>
            ))}
          </div>
        </div>

        {/* No key */}
        {error === "no-key" && (
          <div className="text-center py-16">
            <p className="text-zinc-400 mb-2">No API key set.</p>
            <p className="text-zinc-600 text-[13px]">Click &quot;Active API Key&quot; in the sidebar to add one.</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-48 rounded-xl bg-white/[0.03] border border-white/[0.06] animate-pulse" />
            ))}
          </div>
        )}

        {/* Categories grid */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 animate-fade-in">
            {filtered.map(({ name, tools }) => {
              const meta = CATEGORY_META[name] || { icon: Package, color: "text-zinc-400", label: name };
              const Icon = meta.icon;
              return (
                <div key={name} className="rounded-xl border border-white/[0.07] bg-[#111113] overflow-hidden hover:border-white/[0.12] transition-colors">
                  <div className="px-4 py-3 border-b border-white/[0.06] flex items-center gap-2.5">
                    <Icon size={15} className={meta.color} />
                    <span className="text-[13px] font-semibold text-white">{meta.label}</span>
                    <span className="ml-auto text-[11px] text-zinc-600 font-mono">{tools.length}</span>
                  </div>
                  <div className="p-3 space-y-2">
                    {tools.map(tool => <ToolCard key={tool.slug} tool={tool} />)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
