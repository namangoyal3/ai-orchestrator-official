"use client";
import { useState, useEffect } from "react";
import { Store, Sparkles, Bot, Wrench, Cpu, ChevronRight, Search, ListFilter as Filter, Loader as Loader2, CircleCheck as CheckCircle2, ArrowRight, Code as Code2, Copy, Check, Zap, Globe, Brain, ChartBar as BarChart3 } from "lucide-react";
import clsx from "clsx";
import { marketplaceApi, type AgentInfo, type ToolInfo, type LLMCard, type RepoCard, type FlowRecommendation } from "@/lib/api";
import { fetchAgents, fetchTools, fetchLLMs, fetchRepos } from "@/lib/supabase-data";

// ─── Category colours ──────────────────────────────────────────────────────

const CAT_COLORS: Record<string, string> = {
  Research:    "bg-blue-900/30 border-blue-700/40 text-blue-300",
  Engineering: "bg-violet-900/30 border-violet-700/40 text-violet-300",
  Analytics:   "bg-amber-900/30 border-amber-700/40 text-amber-300",
  Documents:   "bg-emerald-900/30 border-emerald-700/40 text-emerald-300",
  Support:     "bg-pink-900/30 border-pink-700/40 text-pink-300",
  Content:     "bg-orange-900/30 border-orange-700/40 text-orange-300",
  Strategy:    "bg-cyan-900/30 border-cyan-700/40 text-cyan-300",
  Web:         "bg-sky-900/30 border-sky-700/40 text-sky-300",
  Data:        "bg-teal-900/30 border-teal-700/40 text-teal-300",
  API:         "bg-purple-900/30 border-purple-700/40 text-purple-300",
  NLP:         "bg-rose-900/30 border-rose-700/40 text-rose-300",
  Integrations:"bg-indigo-900/30 border-indigo-700/40 text-indigo-300",
};

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: "text-violet-400",
  openai:    "text-emerald-400",
  google:    "text-blue-400",
};

const FLOW_TYPE_COLORS: Record<string, string> = {
  input:  "border-slate-600 bg-slate-800/60",
  llm:    "border-violet-500/50 bg-violet-900/20",
  agent:  "border-indigo-500/50 bg-indigo-900/20",
  tool:   "border-emerald-500/50 bg-emerald-900/20",
  output: "border-amber-500/50 bg-amber-900/20",
};

// ─── Sub-components ────────────────────────────────────────────────────────

function CategoryBadge({ cat }: { cat: string }) {
  const cls = CAT_COLORS[cat] ?? "bg-slate-800 border-slate-700 text-slate-400";
  return (
    <span className={clsx("text-[10px] font-semibold px-2 py-0.5 rounded-full border", cls)}>
      {cat}
    </span>
  );
}

function AgentCard({ agent }: { agent: AgentInfo }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-indigo-500/40 transition-all group">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-xl group-hover:border-indigo-500/40 transition-all">
          {agent.icon}
        </div>
        <CategoryBadge cat={agent.category} />
      </div>
      <h3 className="font-semibold text-white text-sm mb-1">{agent.name}</h3>
      <p className="text-xs text-slate-500 leading-relaxed mb-3 line-clamp-2">{agent.description}</p>
      <div className="flex flex-wrap gap-1">
        {agent.capabilities.slice(0, 3).map(cap => (
          <span key={cap} className="text-[10px] bg-slate-800 text-slate-500 px-2 py-0.5 rounded-full border border-slate-700">
            {cap.replace(/_/g, " ")}
          </span>
        ))}
        {agent.capabilities.length > 3 && (
          <span className="text-[10px] text-slate-600 px-2 py-0.5">+{agent.capabilities.length - 3}</span>
        )}
      </div>
      <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between">
        <span className="text-[10px] text-slate-600 font-mono">{agent.preferred_llm.split("-").slice(0,2).join("-")}</span>
        <span className="text-[10px] text-emerald-500 font-semibold">Built-in</span>
      </div>
    </div>
  );
}

function ToolCard({ tool }: { tool: ToolInfo }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/40 transition-all group">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-xl group-hover:border-emerald-500/40 transition-all">
          {tool.icon}
        </div>
        <CategoryBadge cat={tool.category} />
      </div>
      <h3 className="font-semibold text-white text-sm mb-1">{tool.name}</h3>
      <p className="text-xs text-slate-500 leading-relaxed mb-3 line-clamp-2">{tool.description}</p>
      <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between">
        <span className="text-[10px] text-slate-600">
          {Object.keys(tool.parameters).length} params
        </span>
        {tool.requires_auth ? (
          <span className="text-[10px] text-amber-500 font-semibold">Auth required</span>
        ) : (
          <span className="text-[10px] text-emerald-500 font-semibold">No auth</span>
        )}
      </div>
    </div>
  );
}

function LLMCardComp({ llm }: { llm: LLMCard }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-violet-500/40 transition-all group">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center group-hover:border-violet-500/40 transition-all">
          <Cpu size={18} className="text-slate-400 group-hover:text-violet-400 transition-colors" />
        </div>
        <span className={clsx("text-[10px] font-semibold uppercase", PROVIDER_COLORS[llm.provider] ?? "text-slate-400")}>
          {llm.provider}
        </span>
      </div>
      <h3 className="font-semibold text-white text-sm mb-1">{llm.display_name}</h3>
      <p className="text-xs text-slate-500 leading-relaxed mb-3 line-clamp-2">{llm.description}</p>
      <div className="flex flex-wrap gap-1 mb-3">
        {llm.best_for.slice(0, 3).map(b => (
          <span key={b} className="text-[10px] bg-slate-800 text-slate-500 px-2 py-0.5 rounded-full border border-slate-700">{b}</span>
        ))}
      </div>
      <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px]">
        <span className="text-slate-600">${llm.pricing.input_per_1m}/1M in</span>
        <span className="text-slate-600">${llm.pricing.output_per_1m}/1M out</span>
      </div>
    </div>
  );
}

function RepoCardComp({ repo }: { repo: RepoCard }) {
  const formatNumber = (n: number) => {
    if (n >= 1000) return (n / 1000).toFixed(1) + "k";
    return n.toString();
  };

  return (
    <a href={repo.url} target="_blank" rel="noopener noreferrer" className="block bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-orange-500/40 transition-all group cursor-pointer h-full">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center group-hover:border-orange-500/40 transition-all">
          <Code2 size={18} className="text-slate-400 group-hover:text-orange-400 transition-colors" />
        </div>
        <CategoryBadge cat={repo.language.toUpperCase()} />
      </div>
      <h3 className="font-semibold text-white text-sm mb-1">{repo.full_name}</h3>
      <p className="text-xs text-slate-500 leading-relaxed mb-3 line-clamp-2">{repo.description || "No description provided."}</p>
      <div className="flex flex-wrap gap-1 mb-3">
        {repo.topics.slice(0, 3).map(t => (
          <span key={t} className="text-[10px] bg-slate-800 text-slate-500 px-2 py-0.5 rounded-full border border-slate-700">{t}</span>
        ))}
      </div>
      <div className="mt-auto pt-3 border-t border-slate-800 flex items-center gap-4 text-[11px] text-slate-400">
        <div className="flex items-center gap-1">
          <Sparkles size={12} className="text-amber-400" />
          {formatNumber(repo.stars)}
        </div>
        <div className="flex items-center gap-1">
          <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" className="text-slate-500"><path fillRule="evenodd" d="M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"></path></svg>
          {formatNumber(repo.forks)}
        </div>
      </div>
    </a>
  );
}

function FlowVisual({ rec }: { rec: FlowRecommendation }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
        <span className="text-xs font-semibold text-slate-300">Recommended Pipeline</span>
      </div>
      <div className="p-4 flex items-start gap-2 overflow-x-auto">
        {rec.flow_steps.map((step, i) => (
          <div key={step.id} className="flex items-center gap-2 shrink-0">
            <div className={clsx(
              "flex flex-col items-center gap-1.5 border rounded-xl p-3 w-32 transition-all",
              FLOW_TYPE_COLORS[step.type] ?? "border-slate-700 bg-slate-800/40"
            )}>
              <span className="text-xl">{step.icon}</span>
              <span className="text-xs font-semibold text-white text-center leading-tight">{step.label}</span>
              <span className={clsx(
                "text-[9px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded-full",
                step.type === "input"  ? "bg-slate-700 text-slate-400" :
                step.type === "llm"    ? "bg-violet-900/40 text-violet-300" :
                step.type === "agent"  ? "bg-indigo-900/40 text-indigo-300" :
                step.type === "tool"   ? "bg-emerald-900/40 text-emerald-300" :
                                         "bg-amber-900/40 text-amber-300"
              )}>
                {step.type}
              </span>
              <p className="text-[10px] text-slate-500 text-center leading-tight line-clamp-2">{step.description}</p>
            </div>
            {i < rec.flow_steps.length - 1 && (
              <ArrowRight size={16} className="text-slate-600 shrink-0" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ActionPlan({ rec }: { rec: FlowRecommendation }) {
  return (
    <div className="space-y-3">
      {rec.action_plan.map((phase) => (
        <div key={phase.step} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-400">
              {phase.step}
            </div>
            <h4 className="font-semibold text-white text-sm">{phase.title}</h4>
          </div>
          <p className="text-xs text-slate-400 mb-3 leading-relaxed">{phase.description}</p>
          <div className="flex flex-wrap gap-2">
            {phase.agents.map(a => (
              <span key={a} className="text-[11px] bg-indigo-900/20 border border-indigo-700/40 text-indigo-300 px-2 py-0.5 rounded-full">
                🤖 {a}
              </span>
            ))}
            {phase.tools.map(t => (
              <span key={t} className="text-[11px] bg-emerald-900/20 border border-emerald-700/40 text-emerald-300 px-2 py-0.5 rounded-full">
                🔧 {t}
              </span>
            ))}
            <span className="text-[11px] bg-violet-900/20 border border-violet-700/40 text-violet-300 px-2 py-0.5 rounded-full">
              ⚡ {phase.llm}
            </span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-800 text-[11px] text-slate-500">
            <span className="text-slate-600 font-medium">Output: </span>{phase.expected_output}
          </div>
        </div>
      ))}
    </div>
  );
}

function CodeSnippet({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Code2 size={13} className="text-slate-500" />
          <span className="text-[11px] text-slate-500 font-medium">API Integration</span>
        </div>
        <button onClick={copy} className="flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-white transition-colors">
          {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <pre className="p-4 text-xs text-emerald-300 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">
        {code}
      </pre>
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────

type Tab = "browse" | "build";
type BrowseTab = "agents" | "tools" | "llms" | "repos";

export default function MarketplacePage() {
  const [tab, setTab] = useState<Tab>("browse");
  const [browseTab, setBrowseTab] = useState<BrowseTab>("agents");
  const [search, setSearch] = useState("");
  const [catFilter, setCatFilter] = useState("All");

  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [llms, setLlms] = useState<LLMCard[]>([]);
  const [repos, setRepos] = useState<RepoCard[]>([]);
  const [agentCats, setAgentCats] = useState<string[]>([]);
  const [toolCats, setToolCats] = useState<string[]>([]);
  const [repoCats, setRepoCats] = useState<string[]>([]);
  const [loadingBrowse, setLoadingBrowse] = useState(true);

  // Build flow state
  const [productDesc, setProductDesc] = useState("");
  const [useCases, setUseCases] = useState("");
  const [building, setBuilding] = useState(false);
  const [recommendation, setRecommendation] = useState<FlowRecommendation | null>(null);
  const [buildError, setBuildError] = useState("");
  const [resultTab, setResultTab] = useState<"flow" | "plan" | "code">("flow");

  useEffect(() => {
    Promise.all([
      fetchAgents(),
      fetchTools(),
      fetchLLMs(),
      fetchRepos(),
    ]).then(([a, t, l, r]) => {
      setAgents(a.agents);
      setTools(t.tools);
      setLlms(l.llms);
      setRepos(r.repos);
      setAgentCats(a.categories ?? []);
      setToolCats(t.categories ?? []);

      const uniqueLangs = Array.from(new Set(r.repos.map(rp => rp.language.toUpperCase()))).filter(Boolean);
      setRepoCats(uniqueLangs as string[]);
    }).catch(() => {
    }).finally(() => setLoadingBrowse(false));
  }, []);

  const handleBuild = async () => {
    if (!productDesc.trim()) return;
    setBuilding(true);
    setBuildError("");
    setRecommendation(null);
    try {
      const ucList = useCases.split("\n").map(s => s.trim()).filter(Boolean);
      const rec = await marketplaceApi.recommend(productDesc, ucList);
      setRecommendation(rec);
      setResultTab("flow");
    } catch (e: unknown) {
      setBuildError(e instanceof Error ? e.message : "Failed to generate recommendation");
    } finally {
      setBuilding(false);
    }
  };

  const filteredAgents = agents.filter(a =>
    (catFilter === "All" || a.category === catFilter) &&
    (a.name.toLowerCase().includes(search.toLowerCase()) || a.description.toLowerCase().includes(search.toLowerCase()))
  );
  const filteredTools = tools.filter(t =>
    (catFilter === "All" || t.category === catFilter) &&
    (t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase()))
  );
  const filteredLlms = llms.filter(l =>
    l.display_name.toLowerCase().includes(search.toLowerCase())
  );
  const filteredRepos = repos.filter(r =>
    (catFilter === "All" || r.language.toUpperCase() === catFilter) &&
    (r.full_name.toLowerCase().includes(search.toLowerCase()) || (r.description && r.description.toLowerCase().includes(search.toLowerCase())))
  );

  const currentCats = browseTab === "agents" ? agentCats : browseTab === "tools" ? toolCats : browseTab === "repos" ? repoCats : [];

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Store size={15} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white text-base">Marketplace</h1>
              <p className="text-[11px] text-slate-500">Browse & build AI-powered product flows</p>
            </div>
          </div>

          {/* Main tabs */}
          <div className="flex bg-slate-800 rounded-lg p-1 gap-1">
            {(["browse", "build"] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={clsx(
                  "flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all",
                  tab === t
                    ? "bg-indigo-600 text-white shadow"
                    : "text-slate-400 hover:text-white"
                )}
              >
                {t === "browse" ? <Store size={14} /> : <Sparkles size={14} />}
                {t === "browse" ? "Browse" : "Build Flow"}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* ── BROWSE TAB ─────────────────────────────────────────────────── */}
        {tab === "browse" && (
          <div>
            {/* Browse sub-tabs + search */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex gap-2">
                {([
                  { id: "agents", label: "Agents", icon: Bot, count: agents.length },
                  { id: "tools",  label: "Tools",  icon: Wrench, count: tools.length },
                  { id: "llms",   label: "LLMs",   icon: Cpu, count: llms.length },
                  { id: "repos",  label: "Open Source", icon: Code2, count: repos.length },
                ] as { id: BrowseTab; label: string; icon: React.ComponentType<{size?: number; className?: string}>; count: number }[]).map(({ id, label, icon: Icon, count }) => (
                  <button
                    key={id}
                    onClick={() => { setBrowseTab(id); setCatFilter("All"); }}
                    className={clsx(
                      "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border transition-all",
                      browseTab === id
                        ? "bg-indigo-600/20 border-indigo-500/40 text-indigo-300"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
                    )}
                  >
                    <Icon size={14} />
                    {label}
                    <span className={clsx(
                      "text-[10px] px-1.5 py-0.5 rounded-full font-semibold",
                      browseTab === id ? "bg-indigo-600/30 text-indigo-300" : "bg-slate-800 text-slate-500"
                    )}>
                      {count}
                    </span>
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder={`Search ${browseTab}...`}
                    className="bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-4 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 w-56"
                  />
                </div>
              </div>
            </div>

            {/* Category filters */}
            {currentCats.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {["All", ...currentCats].map(cat => (
                  <button
                    key={cat}
                    onClick={() => setCatFilter(cat)}
                    className={clsx(
                      "text-xs px-3 py-1.5 rounded-lg border font-medium transition-all",
                      catFilter === cat
                        ? "bg-indigo-600/20 border-indigo-500/40 text-indigo-300"
                        : "bg-slate-900 border-slate-800 text-slate-500 hover:text-white hover:border-slate-700"
                    )}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            )}

            {loadingBrowse ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 size={24} className="animate-spin text-slate-600" />
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 items-stretch">
                {browseTab === "agents" && filteredAgents.map(a => <AgentCard key={a.slug} agent={a} />)}
                {browseTab === "tools"  && filteredTools.map(t => <ToolCard key={t.slug} tool={t} />)}
                {browseTab === "llms"   && filteredLlms.map(l => <LLMCardComp key={l.id} llm={l} />)}
                {browseTab === "repos"  && filteredRepos.map(r => <RepoCardComp key={r.full_name} repo={r} />)}
              </div>
            )}
          </div>
        )}

        {/* ── BUILD FLOW TAB ──────────────────────────────────────────────── */}
        {tab === "build" && (
          <div className="max-w-4xl mx-auto">
            {!recommendation ? (
              <div className="space-y-6">
                {/* Hero */}
                <div className="text-center py-4">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-600 to-indigo-700 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-indigo-900/40">
                    <Sparkles size={24} className="text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">Build Your Product Flow</h2>
                  <p className="text-slate-400 text-sm max-w-xl mx-auto">
                    Describe your product and we&apos;ll recommend the optimal combination of agents, tools, and LLMs — with a complete action plan and ready-to-use API code.
                  </p>
                </div>

                {/* Input form */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Product Description <span className="text-red-400">*</span>
                    </label>
                    <textarea
                      value={productDesc}
                      onChange={e => setProductDesc(e.target.value)}
                      placeholder="e.g. A B2B SaaS platform that automatically monitors competitor websites, extracts pricing and feature changes, and sends weekly digest emails to sales teams..."
                      rows={5}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 resize-none"
                    />
                    <p className="text-[11px] text-slate-600 mt-1">{productDesc.length} / 5000 characters</p>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Key Use Cases <span className="text-slate-500 font-normal">(optional, one per line)</span>
                    </label>
                    <textarea
                      value={useCases}
                      onChange={e => setUseCases(e.target.value)}
                      placeholder={"Scrape competitor pricing pages daily\nExtract feature bullet points from landing pages\nGenerate comparison reports\nSend Slack alerts on changes"}
                      rows={4}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 resize-none"
                    />
                  </div>

                  {buildError && (
                    <div className="bg-red-900/20 border border-red-700/40 rounded-lg px-4 py-3 text-sm text-red-300">
                      {buildError}
                    </div>
                  )}

                  <button
                    onClick={handleBuild}
                    disabled={building || !productDesc.trim()}
                    className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition-all text-sm"
                  >
                    {building ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        Analyzing product & building flow...
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} />
                        Generate Recommended Flow
                        <ChevronRight size={14} />
                      </>
                    )}
                  </button>
                </div>

                {/* Example products */}
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Try an example</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[
                      { icon: <Globe size={16} />, title: "Competitor Intelligence", desc: "Monitor competitor sites, extract pricing & features, generate weekly reports" },
                      { icon: <BarChart3 size={16} />, title: "Research Assistant", desc: "Deep-dive any topic, synthesize sources, produce structured research reports" },
                      { icon: <Brain size={16} />, title: "Document Q&A Bot", desc: "Upload contracts or manuals, ask questions, extract clauses and summaries" },
                      { icon: <Zap size={16} />, title: "Content Pipeline", desc: "Research trends, draft blog posts, optimize for SEO, schedule publications" },
                    ].map(ex => (
                      <button
                        key={ex.title}
                        onClick={() => setProductDesc(ex.desc)}
                        className="flex items-start gap-3 p-4 bg-slate-900 border border-slate-800 rounded-xl text-left hover:border-indigo-500/40 transition-all group"
                      >
                        <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                          {ex.icon}
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">{ex.title}</div>
                          <div className="text-xs text-slate-500 mt-0.5 leading-relaxed">{ex.desc}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* ── RESULTS ──────────────────────────────────────────────── */
              <div className="space-y-6">
                {/* Summary header */}
                <div className="bg-gradient-to-r from-indigo-900/30 to-purple-900/20 border border-indigo-700/30 rounded-2xl p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle2 size={18} className="text-emerald-400" />
                        <span className="text-sm font-semibold text-emerald-300">Flow Generated</span>
                      </div>
                      <p className="text-white font-semibold text-base mb-1">{recommendation.product_summary}</p>
                      <p className="text-sm text-slate-400">
                        <span className="text-violet-300 font-medium">Primary LLM:</span> {recommendation.recommended_llm} — {recommendation.llm_reason}
                      </p>
                    </div>
                    <button
                      onClick={() => setRecommendation(null)}
                      className="text-xs text-slate-500 hover:text-white border border-slate-700 hover:border-slate-600 px-3 py-1.5 rounded-lg transition-all"
                    >
                      New Flow
                    </button>
                  </div>

                  {/* Quick chips */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    {recommendation.recommended_agents.map(a => (
                      <span key={a.slug} className="flex items-center gap-1.5 text-xs bg-indigo-900/40 border border-indigo-700/40 text-indigo-300 px-3 py-1 rounded-full">
                        {a.icon} {a.name}
                      </span>
                    ))}
                    {recommendation.recommended_tools.map(t => (
                      <span key={t.slug} className="flex items-center gap-1.5 text-xs bg-emerald-900/30 border border-emerald-700/40 text-emerald-300 px-3 py-1 rounded-full">
                        {t.icon} {t.name}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Result tabs */}
                <div className="flex gap-2 border-b border-slate-800 pb-0">
                  {([
                    { id: "flow", label: "Pipeline Flow" },
                    { id: "plan", label: "Action Plan" },
                    { id: "code", label: "API Code" },
                  ] as { id: typeof resultTab; label: string }[]).map(({ id, label }) => (
                    <button
                      key={id}
                      onClick={() => setResultTab(id)}
                      className={clsx(
                        "px-4 py-2.5 text-sm font-medium border-b-2 transition-all -mb-px",
                        resultTab === id
                          ? "border-indigo-400 text-white"
                          : "border-transparent text-slate-500 hover:text-white"
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                {resultTab === "flow" && (
                  <div className="space-y-4">
                    <FlowVisual rec={recommendation} />
                    {/* Agent details */}
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300 mb-3">Why these agents?</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {recommendation.recommended_agents.map(a => (
                          <div key={a.slug} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xl">{a.icon}</span>
                              <span className="font-semibold text-white text-sm">{a.name}</span>
                            </div>
                            <p className="text-xs text-indigo-300 mb-1 font-medium">{a.role_in_flow}</p>
                            <p className="text-xs text-slate-500">{a.reason}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                    {/* Tool details */}
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300 mb-3">Why these tools?</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {recommendation.recommended_tools.map(t => (
                          <div key={t.slug} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xl">{t.icon}</span>
                              <span className="font-semibold text-white text-sm">{t.name}</span>
                            </div>
                            <p className="text-xs text-emerald-300 mb-1 font-medium">Used by: {t.used_by_agent}</p>
                            <p className="text-xs text-slate-500">{t.reason}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {resultTab === "plan" && <ActionPlan rec={recommendation} />}
                {resultTab === "code" && <CodeSnippet code={recommendation.api_snippet} />}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
