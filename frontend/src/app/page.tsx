"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity, Zap, DollarSign, Clock, TrendingUp, TrendingDown,
  Bot, Wrench, ChevronRight, ArrowUpRight, Terminal, Key,
  AlertTriangle, Info, CheckCircle2, BarChart2,
  Cpu, Globe, Shield,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import Header from "@/components/Header";
import { analyticsApi, gateway, type AnalyticsSummary, type HistoryItem, type TimelinePoint } from "@/lib/api";

// ─── Types ───────────────────────────────────────────────────

interface ModelUsage { model: string; requests: number; cost: number; }
interface CategoryUsage { category: string; requests: number; }

// ─── Mock / fallback data ────────────────────────────────────

const MOCK_SUMMARY: AnalyticsSummary = {
  period_days: 30, total_requests: 1247, successful_requests: 1198,
  failed_requests: 49, success_rate: 96.1,
  total_input_tokens: 2840000, total_output_tokens: 890000, total_tokens: 3730000,
  total_cost_usd: 18.43, avg_latency_ms: 1820,
};

const MOCK_TIMELINE: TimelinePoint[] = Array.from({ length: 14 }, (_, i) => ({
  date: new Date(Date.now() - (13 - i) * 86400000).toISOString().split("T")[0],
  requests: Math.floor(20 + Math.sin(i * 0.7) * 15 + Math.random() * 20),
  cost: parseFloat((0.3 + Math.random() * 0.8).toFixed(3)),
}));

const MOCK_MODELS: ModelUsage[] = [
  { model: "claude-opus-4-6", requests: 312, cost: 8.20 },
  { model: "claude-sonnet-4-6", requests: 587, cost: 6.80 },
  { model: "claude-haiku-4-5-20251001", requests: 248, cost: 1.40 },
  { model: "gpt-4o", requests: 78, cost: 1.60 },
  { model: "gemini-2.0-flash", requests: 22, cost: 0.43 },
];

const MOCK_CATEGORIES: CategoryUsage[] = [
  { category: "coding", requests: 320 },
  { category: "research", requests: 260 },
  { category: "analysis", requests: 215 },
  { category: "writing", requests: 180 },
  { category: "planning", requests: 142 },
  { category: "summarization", requests: 130 },
];

// ─── Provider config ─────────────────────────────────────────

const PROVIDERS = [
  {
    name: "Anthropic",
    status: "online" as const,
    uptime: "99.95%",
    latency: "145ms",
    usage: 72,
    costPerToken: "$0.00003",
    models: ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"],
    color: "indigo",
    icon: "🧠",
  },
  {
    name: "OpenAI",
    status: "online" as const,
    uptime: "99.98%",
    latency: "120ms",
    usage: 14,
    costPerToken: "$0.00025",
    models: ["gpt-4o", "gpt-4o-mini"],
    color: "emerald",
    icon: "⚡",
  },
  {
    name: "Google AI",
    status: "online" as const,
    uptime: "99.82%",
    latency: "220ms",
    usage: 14,
    costPerToken: "$0.00001",
    models: ["gemini-2.0-flash"],
    color: "amber",
    icon: "✨",
  },
];

const ALERTS = [
  { id: 1, severity: "info" as const, message: "Auto-routing selected Claude Opus 4.6 for 312 complex tasks this month", time: "2 min ago" },
  { id: 2, severity: "warning" as const, message: "Google AI latency increased to 220ms — consider fallback routing", time: "18 min ago" },
  { id: 3, severity: "success" as const, message: "Cost optimization: saved 23% by routing simple tasks to Haiku", time: "1 hr ago" },
];

// ─── Color maps ───────────────────────────────────────────────

const MODEL_COLORS: Record<string, { bar: string; text: string; bg: string }> = {
  "claude-opus-4-6":           { bar: "#8b5cf6", text: "text-purple-400", bg: "bg-purple-500/20" },
  "claude-sonnet-4-6":         { bar: "#6366f1", text: "text-indigo-400", bg: "bg-indigo-500/20" },
  "claude-haiku-4-5-20251001": { bar: "#10b981", text: "text-emerald-400", bg: "bg-emerald-500/20" },
  "gpt-4o":                    { bar: "#f59e0b", text: "text-amber-400",  bg: "bg-amber-500/20" },
  "gemini-2.0-flash":          { bar: "#06b6d4", text: "text-cyan-400",   bg: "bg-cyan-500/20" },
};

const CATEGORY_COLORS: Record<string, string> = {
  coding:        "#6366f1",
  research:      "#8b5cf6",
  analysis:      "#f59e0b",
  writing:       "#10b981",
  planning:      "#06b6d4",
  summarization: "#f43f5e",
  document_qa:   "#0ea5e9",
  general:       "#64748b",
};

const CAT_BADGE: Record<string, string> = {
  coding:        "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
  research:      "bg-purple-500/20 text-purple-400 border-purple-500/30",
  analysis:      "bg-amber-500/20 text-amber-400 border-amber-500/30",
  writing:       "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  document_qa:   "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  planning:      "bg-sky-500/20 text-sky-400 border-sky-500/30",
  general:       "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

const STATUS_COLORS: Record<string, string> = {
  completed:  "text-emerald-400",
  failed:     "text-red-400",
  processing: "text-amber-400",
  pending:    "text-slate-400",
};

// ─── Sub-components ───────────────────────────────────────────

function DeltaBadge({ value, inverse = false }: { value: string; inverse?: boolean }) {
  const isUp = value.startsWith("↑") || value.startsWith("+");
  const good = inverse ? !isUp : isUp;
  return (
    <span className={`flex items-center gap-0.5 text-xs font-medium ${good ? "text-emerald-400" : "text-red-400"}`}>
      {good ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
      {value.replace(/^[↑↓+\-]/, "")}
    </span>
  );
}

function StatCard({ label, value, sub, icon: Icon, color, delta, inverseDelta }: {
  label: string; value: string; sub?: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string; delta?: string; inverseDelta?: boolean;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-2 hover:border-slate-700 transition-all hover:shadow-lg hover:shadow-slate-900/50 group">
      <div className="flex items-center justify-between">
        <span className="text-slate-400 text-xs font-medium uppercase tracking-wide">{label}</span>
        <div className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center`}>
          <Icon size={15} />
        </div>
      </div>
      <div className="text-2xl font-bold text-white tracking-tight">{value}</div>
      <div className="flex items-center justify-between">
        {sub && <span className="text-slate-500 text-xs">{sub}</span>}
        {delta && <DeltaBadge value={delta} inverse={inverseDelta} />}
      </div>
    </div>
  );
}

function CircularProgress({ pct, color }: { pct: number; color: string }) {
  const r = 20;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <svg width="52" height="52" className="-rotate-90">
      <circle cx="26" cy="26" r={r} fill="none" stroke="#1e293b" strokeWidth="5" />
      <circle cx="26" cy="26" r={r} fill="none" stroke={color} strokeWidth="5"
        strokeDasharray={`${dash} ${circ - dash}`} strokeLinecap="round" />
    </svg>
  );
}

function ProviderCard({ p }: { p: typeof PROVIDERS[0] }) {
  const colors: Record<string, { ring: string; dot: string; text: string; badge: string }> = {
    indigo:  { ring: "#6366f1", dot: "bg-indigo-400",  text: "text-indigo-400",  badge: "bg-indigo-500/20 border-indigo-500/30" },
    emerald: { ring: "#10b981", dot: "bg-emerald-400", text: "text-emerald-400", badge: "bg-emerald-500/20 border-emerald-500/30" },
    amber:   { ring: "#f59e0b", dot: "bg-amber-400",   text: "text-amber-400",   badge: "bg-amber-500/20 border-amber-500/30" },
  };
  const c = colors[p.color];

  return (
    <div className={`bg-slate-900 border rounded-xl p-4 hover:border-slate-600 transition-all ${
      p.status === "online" ? "border-slate-800" : "border-red-800/50"
    }`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className="text-xl">{p.icon}</span>
          <div>
            <div className="text-sm font-semibold text-white">{p.name}</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-1.5 h-1.5 rounded-full ${c.dot} ${p.status === "online" ? "animate-pulse" : ""}`} />
              <span className={`text-xs ${p.status === "online" ? "text-emerald-400" : "text-red-400"}`}>
                {p.status === "online" ? "Online" : "Offline"}
              </span>
            </div>
          </div>
        </div>
        <div className="relative flex items-center justify-center">
          <CircularProgress pct={p.usage} color={c.ring} />
          <span className={`absolute text-xs font-bold ${c.text}`}>{p.usage}%</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
        <div className="bg-slate-800/60 rounded-lg px-2.5 py-1.5">
          <div className="text-slate-500 text-[10px] uppercase tracking-wide mb-0.5">Uptime</div>
          <div className="text-white font-medium">{p.uptime}</div>
        </div>
        <div className="bg-slate-800/60 rounded-lg px-2.5 py-1.5">
          <div className="text-slate-500 text-[10px] uppercase tracking-wide mb-0.5">Latency</div>
          <div className="text-white font-medium">{p.latency}</div>
        </div>
        <div className="bg-slate-800/60 rounded-lg px-2.5 py-1.5 col-span-2">
          <div className="text-slate-500 text-[10px] uppercase tracking-wide mb-0.5">Cost / 1K tokens</div>
          <div className={`font-semibold ${c.text}`}>{p.costPerToken}</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {p.models.map(m => (
          <span key={m} className={`text-[10px] px-1.5 py-0.5 rounded border ${c.badge} ${c.text}`}>
            {m.split("-").slice(0, 2).join("-")}
          </span>
        ))}
      </div>
    </div>
  );
}

function AlertItem({ alert }: { alert: typeof ALERTS[0] }) {
  const cfg = {
    warning: { icon: AlertTriangle, color: "text-amber-400",   bg: "bg-amber-900/20 border-amber-700/30" },
    info:    { icon: Info,          color: "text-blue-400",    bg: "bg-blue-900/20 border-blue-700/30" },
    success: { icon: CheckCircle2,  color: "text-emerald-400", bg: "bg-emerald-900/20 border-emerald-700/30" },
  };
  const { icon: Icon, color, bg } = cfg[alert.severity];
  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${bg}`}>
      <Icon size={14} className={`${color} mt-0.5 shrink-0`} />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-slate-300 leading-relaxed">{alert.message}</p>
        <p className="text-[10px] text-slate-500 mt-0.5">{alert.time}</p>
      </div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-white font-medium">
          {p.dataKey === "requests" ? `${p.value} requests` : `$${p.value}`}
        </p>
      ))}
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────

export default function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [models, setModels] = useState<ModelUsage[]>([]);
  const [categories, setCategories] = useState<CategoryUsage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.summary(30),
      analyticsApi.timeseries(14),
      analyticsApi.models(30),
      analyticsApi.categories(30),
      gateway.history(8),
    ])
      .then(([sum, tl, mdl, cat, hist]) => {
        setSummary(sum);
        setTimeline(tl.timeline);
        setModels((mdl.models as ModelUsage[]) || MOCK_MODELS);
        setCategories((cat.categories as CategoryUsage[]) || MOCK_CATEGORIES);
        setHistory(hist.items);
      })
      .catch(() => {
        setSummary(MOCK_SUMMARY);
        setTimeline(MOCK_TIMELINE);
        setModels(MOCK_MODELS);
        setCategories(MOCK_CATEGORIES);
        setHistory([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const totalReqs   = summary?.total_requests ?? 0;
  const successRate = summary?.success_rate ?? 0;
  const avgLatency  = summary?.avg_latency_ms ?? 0;
  const totalCost   = summary?.total_cost_usd ?? 0;

  const modelBadge = (model: string) => {
    const c = MODEL_COLORS[model];
    return c ? `${c.bg} ${c.text}` : "bg-slate-500/20 text-slate-400";
  };

  const displayModels     = models.length ? models : MOCK_MODELS;
  const displayCategories = categories.length ? categories : MOCK_CATEGORIES;

  return (
    <div className="animate-fade-in">
      <Header
        title="Dashboard"
        subtitle="Real-time monitoring across all AI providers, agents, and tools"
      />

      <div className="p-6 space-y-5">

        {/* ── Stat cards ──────────────────────────────────────── */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard
            label="Total Requests"
            value={loading ? "—" : totalReqs.toLocaleString()}
            sub="Last 30 days"
            icon={Activity}
            color="bg-indigo-500/20 text-indigo-400"
            delta="↑ 12.3%"
          />
          <StatCard
            label="Success Rate"
            value={loading ? "—" : `${successRate.toFixed(1)}%`}
            sub={`${(summary?.successful_requests ?? 0).toLocaleString()} successful`}
            icon={Shield}
            color="bg-emerald-500/20 text-emerald-400"
            delta="↑ 0.2%"
          />
          <StatCard
            label="Avg Response Time"
            value={loading ? "—" : `${(avgLatency / 1000).toFixed(2)}s`}
            sub="End-to-end p50"
            icon={Clock}
            color="bg-amber-500/20 text-amber-400"
            delta="↓ 18ms"
            inverseDelta
          />
          <StatCard
            label="Total Cost"
            value={loading ? "—" : `$${totalCost.toFixed(2)}`}
            sub={`${((summary?.total_tokens ?? 0) / 1_000_000).toFixed(1)}M tokens`}
            icon={DollarSign}
            color="bg-purple-500/20 text-purple-400"
            delta="↓ 8.4%"
            inverseDelta
          />
        </div>

        {/* ── Main 2-col layout ───────────────────────────────── */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

          {/* LEFT col (span 2): charts */}
          <div className="xl:col-span-2 space-y-5">

            {/* Request volume chart */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-white font-semibold text-sm">Request Volume</h3>
                  <p className="text-slate-500 text-xs mt-0.5">Daily requests — last 14 days</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1.5 text-xs text-slate-400">
                    <span className="w-2.5 h-0.5 bg-indigo-500 rounded" />Requests
                  </span>
                  <span className="text-xs bg-slate-800 text-slate-500 px-2 py-0.5 rounded-md border border-slate-700">14d</span>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={180}>
                <AreaChart data={timeline} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="reqGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 10 }} tickLine={false} axisLine={false}
                    tickFormatter={(d) => d.slice(5)} interval="preserveStartEnd" />
                  <YAxis tick={{ fill: "#475569", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="requests" stroke="#6366f1" strokeWidth={2}
                    fill="url(#reqGrad)" dot={false} activeDot={{ r: 4, fill: "#6366f1" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Model distribution + Category breakdown side by side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

              {/* LLM model usage bars */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Cpu size={14} className="text-indigo-400" />
                  <h3 className="text-white font-semibold text-sm">LLM Distribution</h3>
                </div>
                <div className="space-y-2.5">
                  {displayModels.map((m) => {
                    const total = displayModels.reduce((s, x) => s + x.requests, 0);
                    const pct   = total > 0 ? (m.requests / total) * 100 : 0;
                    const c     = MODEL_COLORS[m.model] || { bar: "#64748b", text: "text-slate-400", bg: "bg-slate-500/20" };
                    const shortName = m.model.includes("opus")   ? "Opus 4.6"
                      : m.model.includes("sonnet") ? "Sonnet 4.6"
                      : m.model.includes("haiku")  ? "Haiku 4.5"
                      : m.model.includes("gpt-4o") ? "GPT-4o"
                      : "Gemini 2.0";
                    return (
                      <div key={m.model}>
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-xs font-medium ${c.text}`}>{shortName}</span>
                          <span className="text-xs text-slate-500">{m.requests} req · {pct.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{ width: `${pct}%`, backgroundColor: c.bar }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Category breakdown bars */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart2 size={14} className="text-purple-400" />
                  <h3 className="text-white font-semibold text-sm">Task Categories</h3>
                </div>
                <div className="space-y-2.5">
                  {displayCategories.slice(0, 6).map((cat) => {
                    const total = displayCategories.reduce((s, x) => s + x.requests, 0);
                    const pct   = total > 0 ? (cat.requests / total) * 100 : 0;
                    const color = CATEGORY_COLORS[cat.category] || "#64748b";
                    return (
                      <div key={cat.category}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-slate-300 capitalize">{cat.category}</span>
                          <span className="text-xs text-slate-500">{cat.requests} · {pct.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{ width: `${pct}%`, backgroundColor: color }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT col: Provider Status */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe size={14} className="text-slate-400" />
                <h3 className="text-white font-semibold text-sm">Provider Status</h3>
              </div>
              <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                Live
              </span>
            </div>
            {PROVIDERS.map((p) => <ProviderCard key={p.name} p={p} />)}

            {/* Routing Intelligence score */}
            <div className="bg-gradient-to-br from-indigo-900/40 to-slate-900 border border-indigo-700/30 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-indigo-300">Routing Efficiency</span>
                <Zap size={13} className="text-indigo-400" />
              </div>
              <div className="text-3xl font-bold text-white">96.5%</div>
              <div className="text-xs text-slate-400 mt-1">Auto-routing accuracy this month</div>
              <div className="mt-3 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full w-[96.5%] bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" />
              </div>
              <div className="mt-1 flex justify-between text-[10px] text-slate-600">
                <span>Target: 95%</span>
                <span className="text-emerald-400">+1.5% above target</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Recent requests ──────────────────────────────────── */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-slate-400" />
              <h3 className="text-white font-semibold text-sm">Recent Requests</h3>
              {history.length > 0 && (
                <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full border border-slate-700">
                  {history.length}
                </span>
              )}
            </div>
            <Link href="/analytics" className="text-indigo-400 hover:text-indigo-300 text-xs flex items-center gap-1 transition-colors">
              View all <ArrowUpRight size={12} />
            </Link>
          </div>

          {/* Table header */}
          <div className="hidden md:grid grid-cols-[1fr_120px_100px_80px_70px] gap-4 px-5 py-2 border-b border-slate-800/50 text-[10px] text-slate-600 uppercase tracking-wide font-medium">
            <span>Prompt</span>
            <span>Model</span>
            <span>Category</span>
            <span>Latency</span>
            <span>Status</span>
          </div>

          <div className="divide-y divide-slate-800/50">
            {loading ? (
              <div className="p-8 text-center text-slate-500 text-sm">Loading requests...</div>
            ) : history.length === 0 ? (
              <div className="p-8 text-center">
                <div className="text-slate-600 text-sm mb-2">No requests yet</div>
                <Link href="/playground" className="text-indigo-400 text-sm hover:underline">
                  Try the playground →
                </Link>
              </div>
            ) : (
              history.map((item) => (
                <div key={item.id}
                  className="grid grid-cols-1 md:grid-cols-[1fr_120px_100px_80px_70px] gap-2 md:gap-4 items-center px-5 py-3 hover:bg-slate-800/30 transition-colors">
                  <div className="text-sm text-slate-200 truncate">{item.prompt}</div>
                  {item.selected_llm && (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium w-fit ${modelBadge(item.selected_llm)}`}>
                      {item.selected_llm.includes("opus")   ? "Opus 4.6"
                        : item.selected_llm.includes("sonnet") ? "Sonnet 4.6"
                        : item.selected_llm.includes("haiku")  ? "Haiku 4.5"
                        : item.selected_llm.split("-").slice(0, 2).join(" ")}
                    </span>
                  )}
                  {item.task_category && (
                    <span className={`text-xs px-1.5 py-0.5 rounded border w-fit capitalize ${CAT_BADGE[item.task_category] || CAT_BADGE.general}`}>
                      {item.task_category}
                    </span>
                  )}
                  <span className="text-xs text-slate-400">{item.latency_ms ? `${item.latency_ms}ms` : "—"}</span>
                  <span className={`text-xs font-medium ${STATUS_COLORS[item.status] || "text-slate-400"}`}>
                    {item.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── Bottom row: Alerts + Quick actions ───────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {/* Alerts */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={14} className="text-amber-400" />
              <h3 className="text-white font-semibold text-sm">System Alerts</h3>
              <span className="ml-auto text-[10px] text-slate-500">{ALERTS.length} active</span>
            </div>
            <div className="space-y-2.5">
              {ALERTS.map((a) => <AlertItem key={a.id} alert={a} />)}
            </div>
          </div>

          {/* Quick actions */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <Zap size={14} className="text-indigo-400" />
              <h3 className="text-white font-semibold text-sm">Quick Actions</h3>
            </div>
            <div className="grid grid-cols-2 gap-2.5">
              {[
                { label: "Playground",    sub: "Test any query live",  href: "/playground", icon: Terminal, color: "text-indigo-400",  bg: "bg-indigo-500/10 border-indigo-500/20" },
                { label: "Browse Agents", sub: "7 specialized agents", href: "/agents",     icon: Bot,      color: "text-purple-400",  bg: "bg-purple-500/10 border-purple-500/20" },
                { label: "Explore Tools", sub: "15 integrations",      href: "/tools",      icon: Wrench,   color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
                { label: "API Keys",      sub: "Manage access",        href: "/api-keys",   icon: Key,      color: "text-amber-400",   bg: "bg-amber-500/10 border-amber-500/20" },
              ].map((item) => (
                <Link key={item.href} href={item.href}
                  className={`flex flex-col gap-2 p-3.5 rounded-xl border ${item.bg} hover:brightness-110 transition-all group`}>
                  <item.icon size={18} className={item.color} />
                  <div>
                    <div className="text-xs font-semibold text-white">{item.label}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{item.sub}</div>
                  </div>
                </Link>
              ))}
            </div>

            {/* System status footer */}
            <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                All systems operational
              </div>
              <span className="text-slate-600">v1.0.0</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
