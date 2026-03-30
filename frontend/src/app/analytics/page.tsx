"use client";
import { useEffect, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { TrendingUp, Activity, DollarSign, Clock, Zap } from "lucide-react";
import Header from "@/components/Header";
import { analyticsApi, type AnalyticsSummary, type TimelinePoint } from "@/lib/api";

const COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];

const MOCK_SUMMARY: AnalyticsSummary = {
  period_days: 30, total_requests: 1247, successful_requests: 1198,
  failed_requests: 49, success_rate: 96.1, total_input_tokens: 2840000,
  total_output_tokens: 890000, total_tokens: 3730000,
  total_cost_usd: 18.43, avg_latency_ms: 1820,
};

const MOCK_TIMELINE: TimelinePoint[] = Array.from({ length: 14 }, (_, i) => ({
  date: new Date(Date.now() - (13 - i) * 86400000).toISOString().split("T")[0],
  requests: Math.floor(Math.random() * 80) + 20,
  cost: Math.round(Math.random() * 150) / 100,
}));

const MOCK_MODELS = [
  { model: "claude-sonnet-4-6", requests: 620, cost: 9.30 },
  { model: "claude-opus-4-6", requests: 380, cost: 7.60 },
  { model: "claude-haiku-4-5", requests: 247, cost: 1.53 },
];

const MOCK_CATEGORIES = [
  { category: "research", requests: 312 },
  { category: "coding", requests: 287 },
  { category: "data_analysis", requests: 198 },
  { category: "writing", requests: 176 },
  { category: "document_qa", requests: 154 },
  { category: "general", requests: 120 },
];

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string;
}) => {
  if (active && payload?.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-xs">
        <p className="text-slate-400 mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.name} style={{ color: p.color }} className="font-semibold">
            {p.name}: {typeof p.value === "number" && p.value < 10 ? `$${p.value.toFixed(2)}` : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

function StatCard({ label, value, sub, icon: Icon, color }: {
  label: string; value: string; sub?: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm">{label}</span>
        <div className={`w-9 h-9 rounded-lg ${color} flex items-center justify-center`}>
          <Icon size={17} />
        </div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
    </div>
  );
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary>(MOCK_SUMMARY);
  const [timeline, setTimeline] = useState<TimelinePoint[]>(MOCK_TIMELINE);
  const [models, setModels] = useState(MOCK_MODELS);
  const [categories, setCategories] = useState(MOCK_CATEGORIES);
  const [days, setDays] = useState(30);

  useEffect(() => {
    Promise.all([
      analyticsApi.summary(days),
      analyticsApi.timeseries(14),
      analyticsApi.models(days),
      analyticsApi.categories(days),
    ]).then(([s, t, m, c]) => {
      setSummary(s);
      setTimeline(t.timeline);
      if (m.models.length) setModels(m.models);
      if (c.categories.length) setCategories(c.categories);
    }).catch(() => {
      setSummary(MOCK_SUMMARY);
      setTimeline(MOCK_TIMELINE);
      setModels(MOCK_MODELS);
      setCategories(MOCK_CATEGORIES);
    });
  }, [days]);

  const successRate = summary.success_rate;

  return (
    <div className="animate-fade-in">
      <Header title="Analytics" subtitle="Usage metrics, costs, and performance insights" />

      <div className="p-6 space-y-6">
        {/* Period selector */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">Period:</span>
          {[7, 14, 30, 90].map((d) => (
            <button key={d} onClick={() => setDays(d)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                days === d
                  ? "bg-indigo-600/20 border-indigo-500/50 text-indigo-300"
                  : "bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard label="Total Requests" value={summary.total_requests.toLocaleString()}
            sub={`${days}d period`} icon={Activity} color="bg-indigo-500/20 text-indigo-400" />
          <StatCard label="Success Rate" value={`${successRate.toFixed(1)}%`}
            sub={`${summary.failed_requests} failed`} icon={TrendingUp} color="bg-emerald-500/20 text-emerald-400" />
          <StatCard label="Total Cost" value={`$${summary.total_cost_usd.toFixed(2)}`}
            sub="All providers" icon={DollarSign} color="bg-amber-500/20 text-amber-400" />
          <StatCard label="Avg Latency" value={`${(summary.avg_latency_ms / 1000).toFixed(1)}s`}
            sub="End-to-end" icon={Clock} color="bg-cyan-500/20 text-cyan-400" />
          <StatCard label="Total Tokens" value={`${(summary.total_tokens / 1_000_000).toFixed(1)}M`}
            sub={`${(summary.total_input_tokens / 1_000_000).toFixed(1)}M in / ${(summary.total_output_tokens / 1_000_000).toFixed(1)}M out`}
            icon={Zap} color="bg-purple-500/20 text-purple-400" />
        </div>

        {/* Charts row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Request volume */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-1">Request Volume</h3>
            <p className="text-slate-500 text-xs mb-5">Daily requests over last 14 days</p>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={timeline}>
                <defs>
                  <linearGradient id="aGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false}
                  tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="requests" name="Requests" stroke="#6366f1"
                  strokeWidth={2} fill="url(#aGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Category donut */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-1">Task Categories</h3>
            <p className="text-slate-500 text-xs mb-3">Request breakdown by category</p>
            <ResponsiveContainer width="100%" height={150}>
              <PieChart>
                <Pie data={categories} dataKey="requests" nameKey="category" cx="50%" cy="50%"
                  outerRadius={60} innerRadius={35}>
                  {categories.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v, n) => [v, (n as string).replace(/_/g, " ")]} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1 mt-2">
              {categories.slice(0, 4).map((c, i) => (
                <div key={c.category} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                    <span className="text-slate-400">{c.category.replace(/_/g, " ")}</span>
                  </div>
                  <span className="text-slate-300">{c.requests}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Charts row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Model usage bars */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-1">LLM Usage</h3>
            <p className="text-slate-500 text-xs mb-5">Requests by model</p>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={models} layout="vertical">
                <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="model" tick={{ fill: "#94a3b8", fontSize: 11 }}
                  tickLine={false} axisLine={false} width={130}
                  tickFormatter={(m) => m.replace("claude-", "").replace("-", " ")} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="requests" name="Requests" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Cost breakdown */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-1">Cost Breakdown</h3>
            <p className="text-slate-500 text-xs mb-5">Daily spend over last 14 days</p>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={timeline}>
                <defs>
                  <linearGradient id="cGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false}
                  tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false}
                  tickFormatter={(v) => `$${v.toFixed(1)}`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cost" name="Cost ($)" stroke="#10b981"
                  strokeWidth={2} fill="url(#cGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Token efficiency */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-4">Token Efficiency</h3>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Input Tokens", value: (summary.total_input_tokens / 1_000_000).toFixed(2) + "M", pct: Math.round(summary.total_input_tokens / summary.total_tokens * 100), color: "bg-indigo-500" },
              { label: "Output Tokens", value: (summary.total_output_tokens / 1_000_000).toFixed(2) + "M", pct: Math.round(summary.total_output_tokens / summary.total_tokens * 100), color: "bg-purple-500" },
              { label: "Cost per 1K Tokens", value: `$${(summary.total_cost_usd / (summary.total_tokens / 1000)).toFixed(4)}`, pct: null, color: "bg-emerald-500" },
            ].map((item) => (
              <div key={item.label} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-sm">{item.label}</span>
                  <span className="text-white font-semibold text-sm">{item.value}</span>
                </div>
                {item.pct !== null && (
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.pct}%` }} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
