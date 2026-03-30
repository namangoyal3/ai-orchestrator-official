"use client";
import { useEffect, useState } from "react";
import { Search, ExternalLink, Zap } from "lucide-react";
import Header from "@/components/Header";
import { agentsApi, type AgentInfo } from "@/lib/api";

const CATEGORY_COLORS: Record<string, string> = {
  Research: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  Engineering: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  Analytics: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  Documents: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  Support: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  Content: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  Strategy: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
};

const LLM_LABELS: Record<string, { label: string; color: string }> = {
  "claude-opus-4-6": { label: "Opus 4.6", color: "text-purple-400" },
  "claude-sonnet-4-6": { label: "Sonnet 4.6", color: "text-blue-400" },
  "claude-haiku-4-5": { label: "Haiku 4.5", color: "text-emerald-400" },
  auto: { label: "Auto", color: "text-slate-400" },
};

const MOCK_AGENTS: AgentInfo[] = [
  {
    slug: "research", name: "Research Agent", description: "Deep research on any topic — searches the web, scrapes sources, synthesizes findings into structured reports.",
    category: "Research", icon: "🔬", capabilities: ["web_search", "url_scraping", "document_analysis", "fact_checking", "citation_generation"],
    required_tools: ["web_search", "web_scrape"], preferred_llm: "claude-sonnet-4-6", is_builtin: true,
  },
  {
    slug: "code", name: "Code Agent", description: "Write, review, debug, and explain code in any programming language. Understands architecture and best practices.",
    category: "Engineering", icon: "💻", capabilities: ["code_generation", "code_review", "debugging", "refactoring", "documentation"],
    required_tools: ["web_search", "github_repo_info"], preferred_llm: "claude-opus-4-6", is_builtin: true,
  },
  {
    slug: "data_analysis", name: "Data Analysis Agent", description: "Analyze data, generate insights, create visualizations, and build statistical models from any dataset.",
    category: "Analytics", icon: "📊", capabilities: ["statistical_analysis", "data_visualization", "trend_detection", "forecasting"],
    required_tools: ["calculator", "json_query", "sql_query"], preferred_llm: "claude-opus-4-6", is_builtin: true,
  },
  {
    slug: "document_qa", name: "Document Q&A Agent", description: "Intelligent Q&A over any document — contracts, reports, manuals, research papers.",
    category: "Documents", icon: "📚", capabilities: ["document_parsing", "qa_extraction", "comparison", "summarization"],
    required_tools: ["parse_pdf", "parse_docx", "web_scrape", "extract_entities"], preferred_llm: "claude-sonnet-4-6", is_builtin: true,
  },
  {
    slug: "customer_support", name: "Customer Support Agent", description: "Empathetic, efficient customer support — handles inquiries, troubleshoots issues, and escalates when needed.",
    category: "Support", icon: "🎯", capabilities: ["issue_resolution", "empathetic_communication", "knowledge_base_search"],
    required_tools: ["web_search", "http_request"], preferred_llm: "claude-sonnet-4-6", is_builtin: true,
  },
  {
    slug: "content_writer", name: "Content Writer Agent", description: "Create compelling content — blog posts, marketing copy, social media, emails, product descriptions.",
    category: "Content", icon: "✍️", capabilities: ["blog_writing", "marketing_copy", "social_media", "seo_optimization"],
    required_tools: ["web_search", "web_scrape"], preferred_llm: "claude-sonnet-4-6", is_builtin: true,
  },
  {
    slug: "planning", name: "Planning & Strategy Agent", description: "Strategic planning, project breakdowns, roadmaps, OKR setting, and execution frameworks for any goal.",
    category: "Strategy", icon: "🗺️", capabilities: ["project_planning", "goal_setting", "risk_analysis", "timeline_creation"],
    required_tools: ["web_search", "calculator"], preferred_llm: "claude-opus-4-6", is_builtin: true,
  },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>(MOCK_AGENTS);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selected, setSelected] = useState<AgentInfo | null>(null);

  useEffect(() => {
    agentsApi.list().then((d) => setAgents(d.agents)).catch(() => setAgents(MOCK_AGENTS));
  }, []);

  const categories = ["All", ...Array.from(new Set(agents.map((a) => a.category)))];
  const filtered = agents.filter((a) => {
    const matchSearch = !search || a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.description.toLowerCase().includes(search.toLowerCase());
    const matchCat = selectedCategory === "All" || a.category === selectedCategory;
    return matchSearch && matchCat;
  });

  return (
    <div className="animate-fade-in">
      <Header title="Agents" subtitle={`${agents.length} specialized AI agents available`} />

      <div className="p-6 space-y-5">
        {/* Search + filter */}
        <div className="flex items-center gap-3">
          <div className="flex-1 flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5">
            <Search size={15} className="text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search agents..."
              className="flex-1 bg-transparent text-slate-300 text-sm outline-none placeholder-slate-600"
            />
          </div>
          <div className="flex gap-2">
            {categories.map((cat) => (
              <button key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`text-xs px-3 py-2 rounded-lg border transition-all whitespace-nowrap ${
                  selectedCategory === cat
                    ? "bg-indigo-600/20 border-indigo-500/50 text-indigo-300"
                    : "bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((agent) => {
            const llmInfo = LLM_LABELS[agent.preferred_llm] || { label: agent.preferred_llm, color: "text-slate-400" };
            const catColor = CATEGORY_COLORS[agent.category] || "bg-slate-500/20 text-slate-400 border-slate-500/30";
            return (
              <div
                key={agent.slug}
                onClick={() => setSelected(selected?.slug === agent.slug ? null : agent)}
                className="bg-slate-900 border border-slate-800 hover:border-slate-600 rounded-xl p-5 cursor-pointer transition-all hover:bg-slate-900/80 group"
              >
                <div className="flex items-start gap-3 mb-3">
                  <span className="text-2xl">{agent.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-white font-semibold text-sm">{agent.name}</h3>
                      {agent.is_builtin && (
                        <span className="text-xs bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded">Built-in</span>
                      )}
                    </div>
                    <span className={`text-xs border px-2 py-0.5 rounded-full mt-1 inline-block ${catColor}`}>
                      {agent.category}
                    </span>
                  </div>
                </div>

                <p className="text-slate-400 text-sm leading-relaxed mb-4">{agent.description}</p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Zap size={11} className="text-slate-600" />
                    <span className={`text-xs font-medium ${llmInfo.color}`}>{llmInfo.label}</span>
                  </div>
                  <span className="text-xs text-slate-600 group-hover:text-slate-400 transition-colors">
                    {agent.capabilities.length} capabilities
                  </span>
                </div>

                {/* Expanded details */}
                {selected?.slug === agent.slug && (
                  <div className="mt-4 pt-4 border-t border-slate-700 space-y-3 animate-fade-in">
                    <div>
                      <div className="text-xs text-slate-500 mb-1.5">Capabilities</div>
                      <div className="flex flex-wrap gap-1">
                        {agent.capabilities.map((c) => (
                          <span key={c} className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                            {c.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1.5">Required Tools</div>
                      <div className="flex flex-wrap gap-1">
                        {agent.required_tools.map((t) => (
                          <span key={t} className="text-xs bg-indigo-900/30 text-indigo-400 border border-indigo-700/40 px-2 py-0.5 rounded">
                            {t.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </div>
                    <a href="/playground" className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
                      <ExternalLink size={12} />
                      Try in playground with agent: {agent.slug}
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
