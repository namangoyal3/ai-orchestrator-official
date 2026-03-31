"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity, Zap, DollarSign, Clock, TrendingUp, TrendingDown,
  Bot, Wrench, ChevronRight, ArrowUpRight, Terminal, Key,
  BarChart2, Cpu, Globe, Shield,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import Header from "@/components/Header";
import { analyticsApi, gateway, type AnalyticsSummary, type HistoryItem, type TimelinePoint } from "@/lib/api";

// ─── Types ───────────────────────────────────────────────────

interface ModelUsage { model: string; display_name: string; requests: number; cost: number; }
interface CategoryUsage { category: string; requests: number; }

// ─── Color maps ───────────────────────────────────────────────

const MODEL_COLORS: Record<string, { bar: string; text: string; bg: string }> = {
  // Direct Anthropic
  "claude-opus-4-6":           { bar: "#8b5cf6", text: "text-purple-600",  bg: "bg-purple-100" },
  "claude-sonnet-4-6":         { bar: "#6366f1", text: "text-indigo-600",  bg: "bg-indigo-100" },
  "claude-haiku-4-5-20251001": { bar: "#10b981", text: "text-emerald-600", bg: "bg-emerald-100" },
  // Direct OpenAI
  "gpt-4o":                    { bar: "#f59e0b", text: "text-amber-600",   bg: "bg-amber-100" },
  "gpt-4o-mini":               { bar: "#fb923c", text: "text-orange-600",  bg: "bg-orange-100" },
  // Google
  "gemini-2.0-flash":          { bar: "#06b6d4", text: "text-cyan-600",    bg: "bg-cyan-100" },
  // OpenRouter model IDs
  "openai/gpt-4o":             { bar: "#f59e0b", text: "text-amber-600",   bg: "bg-amber-100" },
  "openai/gpt-4o-mini":        { bar: "#fb923c", text: "text-orange-600",  bg: "bg-orange-100" },
  "anthropic/claude-3-5-sonnet":       { bar: "#6366f1", text: "text-indigo-600",  bg: "bg-indigo-100" },
  "anthropic/claude-3-5-sonnet-20241022": { bar: "#6366f1", text: "text-indigo-600", bg: "bg-indigo-100" },
  "anthropic/claude-3-haiku":  { bar: "#10b981", text: "text-emerald-600", bg: "bg-emerald-100" },
  "meta-llama/llama-3.1-70b-instruct": { bar: "#ec4899", text: "text-pink-600",    bg: "bg-pink-100" },
  "meta-llama/llama-3.1-8b-instruct":  { bar: "#f43f5e", text: "text-rose-600",    bg: "bg-rose-100" },
  "mistralai/mistral-7b-instruct":     { bar: "#0ea5e9", text: "text-sky-600",     bg: "bg-sky-100" },
  "google/gemini-pro":         { bar: "#06b6d4", text: "text-cyan-600",    bg: "bg-cyan-100" },
  "google/gemini-flash-1.5":   { bar: "#22d3ee", text: "text-cyan-600",    bg: "bg-cyan-100" },
};

const CATEGORY_COLORS: Record<string, string> = {
  coding:        "#6366f1",
  research:      "#8b5cf6",
  analysis:      "#f59e0b",
  writing:       "#10b981",
  planning:      "#06b6d4",
  summarization: "#f43f5e",
  document_qa:   "#0ea5e9",
  general:       "#94a3b8",
};

const CAT_BADGE: Record<string, string> = {
  coding:        "bg-indigo-100 text-indigo-700 border-indigo-200",
  research:      "bg-purple-100 text-purple-700 border-purple-200",
  analysis:      "bg-amber-100 text-amber-700 border-amber-200",
  writing:       "bg-emerald-100 text-emerald-700 border-emerald-200",
  document_qa:   "bg-cyan-100 text-cyan-700 border-cyan-200",
  planning:      "bg-sky-100 text-sky-700 border-sky-200",
  general:       "bg-slate-100 text-slate-600 border-slate-200",
};

const STATUS_COLORS: Record<string, string> = {
  completed:  "text-emerald-600",
  failed:     "text-red-500",
  processing: "text-amber-600",
  pending:    "text-slate-400",
};

// ─── Sub-components ───────────────────────────────────────────

function DeltaBadge({ value, inverse = false }: { value: string; inverse?: boolean }) {
  const isUp = value.startsWith("↑") || value.startsWith("+");
  const good = inverse ? !isUp : isUp;
  return (
    <span className={`flex items-center gap-0.5 text-xs font-medium ${good ? "text-emerald-600" : "text-red-500"}`}>
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
    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col gap-2 hover:border-slate-300 transition-all hover:shadow-sm group">
      <div className="flex items-center justify-between">
        <span className="text-slate-500 text-xs font-medium uppercase tracking-wide">{label}</span>
        <div className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center`}>
          <Icon size={15} />
        </div>
      </div>
      <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
      <div className="flex items-center justify-between">
        {sub && <span className="text-slate-400 text-xs">{sub}</span>}
        {delta && <DeltaBadge value={delta} inverse={inverseDelta} />}
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
    <div className="bg-white border border-slate-200 rounded-lg p-3 text-xs shadow-lg">
      <p className="text-slate-500 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-slate-900 font-medium">
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
  const [apiError, setApiError] = useState(false);

  useEffect(() => {
    Promise.allSettled([
      analyticsApi.summary(30),
      analyticsApi.timeseries(14),
      analyticsApi.models(30),
      analyticsApi.categories(30),
      gateway.history(8),
    ]).then(([sumR, tlR, mdlR, catR, histR]) => {
      let anySuccess = false;
      if (sumR.status === "fulfilled")  { setSummary(sumR.value); anySuccess = true; }
      if (tlR.status === "fulfilled")   { setTimeline(tlR.value.timeline); anySuccess = true; }
      if (mdlR.status === "fulfilled")  { setModels(mdlR.value.models as ModelUsage[]); anySuccess = true; }
      if (catR.status === "fulfilled")  { setCategories(catR.value.categories as CategoryUsage[]); anySuccess = true; }
      if (histR.status === "fulfilled") { setHistory(histR.value.items); anySuccess = true; }
      if (!anySuccess) setApiError(true);
    }).finally(() => setLoading(false));
  }, []);

  const totalReqs   = summary?.total_requests ?? 0;
  const successRate = summary?.success_rate ?? 0;
  const avgLatency  = summary?.avg_latency_ms ?? 0;
  const totalCost   = summary?.total_cost_usd ?? 0;

  const modelBadge = (model: string) => {
    const c = MODEL_COLORS[model];
    return c ? `${c.bg} ${c.text}` : "bg-slate-100 text-slate-600";
  };

  const modelShortName = (model: string, displayName?: string) => {
    if (displayName) return displayName;
    if (model.includes("opus"))   return "Opus 4.6";
    if (model.includes("sonnet")) return "Sonnet";
    if (model.includes("haiku"))  return "Haiku";
    if (model.includes("gpt-4o-mini")) return "GPT-4o Mini";
    if (model.includes("gpt-4o")) return "GPT-4o";
    if (model.includes("gemini")) return "Gemini";
    const short = model.split("/").pop() || model;
    return short.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <div className="animate-fade-in">
      <Header
        title="Dashboard"
        subtitle="Real-time monitoring across all AI providers, agents, and tools"
      />

      <div className="p-6 space-y-5">

        {/* API connection error banner */}
        {apiError && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
            <span className="text-amber-500 text-sm font-medium">⚠️</span>
            <div>
              <p className="text-amber-800 text-sm font-medium">Cannot reach the gateway API</p>
              <p className="text-amber-600 text-xs mt-0.5">
                Check your API key in settings or ensure the backend is running.
              </p>
            </div>
          </div>
        )}

        {/* Stat cards */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard
            label="Total Requests"
            value={loading ? "—" : totalReqs.toLocaleString()}
            sub="Last 30 days"
            icon={Activity}
            color="bg-indigo-100 text-indigo-600"
            delta={totalReqs > 0 ? "↑ active" : undefined}
          />
          <StatCard
            label="Success Rate"
            value={loading ? "—" : totalReqs > 0 ? `${successRate.toFixed(1)}%` : "—"}
            sub={totalReqs > 0 ? `${(summary?.successful_requests ?? 0).toLocaleString()} successful` : "No data yet"}
            icon={Shield}
            color="bg-emerald-100 text-emerald-600"
          />
          <StatCard
            label="Avg Response Time"
            value={loading ? "—" : avgLatency > 0 ? `${(avgLatency / 1000).toFixed(2)}s` : "—"}
            sub="End-to-end p50"
            icon={Clock}
            color="bg-amber-100 text-amber-600"
          />
          <StatCard
            label="Total Cost"
            value={loading ? "—" : totalCost > 0 ? `$${totalCost.toFixed(2)}` : "$0.00"}
            sub={totalCost > 0 ? `${((summary?.total_tokens ?? 0) / 1_000_000).toFixed(1)}M tokens` : "No usage yet"}
            icon={DollarSign}
            color="bg-purple-100 text-purple-600"
          />
        </div>

        {/* Main 2-col layout */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

          {/* LEFT col (span 2): charts */}
          <div className="xl:col-span-2 space-y-5">

            {/* Request volume chart */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-slate-900 font-semibold text-sm">Request Volume</h3>
                  <p className="text-slate-400 text-xs mt-0.5">Daily requests — last 14 days</p>
                </div>
                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-md border border-slate-200">14d</span>
              </div>
              {timeline.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <AreaChart data={timeline} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="reqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 10 }} tickLine={false} axisLine={false}
                      tickFormatter={(d) => d.slice(5)} interval="preserveStartEnd" />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="requests" stroke="#6366f1" strokeWidth={2}
                      fill="url(#reqGrad)" dot={false} activeDot={{ r: 4, fill: "#6366f1" }} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[180px] flex items-center justify-center text-slate-400 text-sm">
                  {loading ? "Loading..." : "No requests yet — try the playground"}
                </div>
              )}
            </div>

            {/* Model distribution + Category breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

              {/* LLM model usage bars */}
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Cpu size={14} className="text-indigo-500" />
                  <h3 className="text-slate-900 font-semibold text-sm">LLM Distribution</h3>
                </div>
                {models.length > 0 ? (
                  <div className="space-y-2.5">
                    {models.map((m) => {
                      const total = models.reduce((s, x) => s + x.requests, 0);
                      const pct   = total > 0 ? (m.requests / total) * 100 : 0;
                      const c     = MODEL_COLORS[m.model] || { bar: "#94a3b8", text: "text-slate-500", bg: "bg-slate-100" };
                      const name  = modelShortName(m.model, m.display_name);
                      return (
                        <div key={m.model}>
                          <div className="flex items-center justify-between mb-1">
                            <span className={`text-xs font-medium ${c.text}`}>{name}</span>
                            <span className="text-xs text-slate-400">{m.requests} req · {pct.toFixed(0)}%</span>
                          </div>
                          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all duration-700"
                              style={{ width: `${pct}%`, backgroundColor: c.bar }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-24 text-slate-400 text-sm">
                    {loading ? "Loading..." : "No model data yet"}
                  </div>
                )}
              </div>

              {/* Category breakdown bars */}
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart2 size={14} className="text-purple-500" />
                  <h3 className="text-slate-900 font-semibold text-sm">Task Categories</h3>
                </div>
                {categories.length > 0 ? (
                  <div className="space-y-2.5">
                    {categories.slice(0, 6).map((cat) => {
                      const total = categories.reduce((s, x) => s + x.requests, 0);
                      const pct   = total > 0 ? (cat.requests / total) * 100 : 0;
                      const color = CATEGORY_COLORS[cat.category] || "#94a3b8";
                      return (
                        <div key={cat.category}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-slate-700 capitalize">{cat.category}</span>
                            <span className="text-xs text-slate-400">{cat.requests} · {pct.toFixed(0)}%</span>
                          </div>
                          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all duration-700"
                              style={{ width: `${pct}%`, backgroundColor: color }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-24 text-slate-400 text-sm">
                    {loading ? "Loading..." : "No category data yet"}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT col: Top Models + Routing Score */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe size={14} className="text-slate-400" />
                <h3 className="text-slate-900 font-semibold text-sm">Top Models</h3>
              </div>
              <span className="text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                Live
              </span>
            </div>

            {models.length > 0 ? (
              models.slice(0, 3).map((m) => {
                const c = MODEL_COLORS[m.model] || { bar: "#94a3b8", text: "text-slate-500", bg: "bg-slate-100" };
                const name = modelShortName(m.model, m.display_name);
                return (
                  <div key={m.model} className="bg-white border border-slate-200 rounded-xl p-4 hover:border-slate-300 transition-all">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-lg ${c.bg} flex items-center justify-center`}>
                          <Cpu size={14} className={c.text} />
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-slate-900">{name}</div>
                          <div className="flex items-center gap-1 mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-xs text-emerald-600">Active</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-slate-50 rounded-lg px-2.5 py-1.5">
                        <div className="text-slate-400 text-[10px] uppercase tracking-wide mb-0.5">Requests</div>
                        <div className="text-slate-900 font-medium">{m.requests.toLocaleString()}</div>
                      </div>
                      <div className="bg-slate-50 rounded-lg px-2.5 py-1.5">
                        <div className="text-slate-400 text-[10px] uppercase tracking-wide mb-0.5">Cost</div>
                        <div className={`font-semibold ${c.text}`}>${m.cost.toFixed(3)}</div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="bg-white border border-slate-200 rounded-xl p-8 flex flex-col items-center justify-center text-center gap-2">
                <Cpu size={24} className="text-slate-300" />
                <p className="text-slate-500 text-sm font-medium">No model data yet</p>
                <Link href="/playground" className="text-indigo-600 text-xs hover:underline">
                  Run a query to see models →
                </Link>
              </div>
            )}

            {/* Routing score */}
            <div className="bg-gradient-to-br from-indigo-50 to-white border border-indigo-100 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-indigo-700">Routing Efficiency</span>
                <Zap size={13} className="text-indigo-500" />
              </div>
              <div className="text-3xl font-bold text-slate-900">
                {totalReqs > 0 ? `${successRate.toFixed(1)}%` : "—"}
              </div>
              <div className="text-xs text-slate-500 mt-1">Success rate this period</div>
              <div className="mt-3 h-1.5 bg-indigo-100 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-700"
                  style={{ width: `${successRate}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Recent requests */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-slate-400" />
              <h3 className="text-slate-900 font-semibold text-sm">Recent Requests</h3>
              {history.length > 0 && (
                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full border border-slate-200">
                  {history.length}
                </span>
              )}
            </div>
            <Link href="/analytics" className="text-indigo-600 hover:text-indigo-500 text-xs flex items-center gap-1 transition-colors">
              View all <ArrowUpRight size={12} />
            </Link>
          </div>

          <div className="hidden md:grid grid-cols-[1fr_120px_100px_80px_70px] gap-4 px-5 py-2 border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wide font-medium">
            <span>Prompt</span><span>Model</span><span>Category</span><span>Latency</span><span>Status</span>
          </div>

          <div className="divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 text-center text-slate-400 text-sm">Loading requests...</div>
            ) : history.length === 0 ? (
              <div className="p-8 text-center">
                <div className="text-slate-400 text-sm mb-2">No requests yet</div>
                <Link href="/playground" className="text-indigo-600 text-sm hover:underline">
                  Try the playground →
                </Link>
              </div>
            ) : (
              history.map((item) => (
                <div key={item.id}
                  className="grid grid-cols-1 md:grid-cols-[1fr_120px_100px_80px_70px] gap-2 md:gap-4 items-center px-5 py-3 hover:bg-slate-50 transition-colors">
                  <div className="text-sm text-slate-800 truncate">{item.prompt}</div>
                  {item.selected_llm && (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium w-fit ${modelBadge(item.selected_llm)}`}>
                      {modelShortName(item.selected_llm)}
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

        {/* Bottom row: Quick actions */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={14} className="text-indigo-500" />
            <h3 className="text-slate-900 font-semibold text-sm">Quick Actions</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
            {[
              { label: "Playground",    sub: "Test any query live",  href: "/playground", icon: Terminal, color: "text-indigo-600",  bg: "bg-indigo-50 border-indigo-100" },
              { label: "Browse Agents", sub: "7 specialized agents", href: "/agents",     icon: Bot,      color: "text-purple-600",  bg: "bg-purple-50 border-purple-100" },
              { label: "Explore Tools", sub: "15 integrations",      href: "/tools",      icon: Wrench,   color: "text-emerald-600", bg: "bg-emerald-50 border-emerald-100" },
              { label: "API Keys",      sub: "Manage access",        href: "/api-keys",   icon: Key,      color: "text-amber-600",   bg: "bg-amber-50 border-amber-100" },
            ].map((item) => (
              <Link key={item.href} href={item.href}
                className={`flex flex-col gap-2 p-3.5 rounded-xl border ${item.bg} hover:brightness-95 transition-all group`}>
                <item.icon size={18} className={item.color} />
                <div>
                  <div className="text-xs font-semibold text-slate-900">{item.label}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{item.sub}</div>
                </div>
                <ChevronRight size={12} className={`${item.color} opacity-0 group-hover:opacity-100 transition-opacity self-end`} />
              </Link>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 text-emerald-600">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              All systems operational
            </div>
            <span className="text-slate-400">v1.0.0</span>
          </div>
        </div>

      </div>
    </div>
  );
}
