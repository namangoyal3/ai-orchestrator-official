"use client";
import { useEffect, useState } from "react";
import { Search, Play, Loader2, ChevronDown, ChevronUp, CheckCircle, XCircle } from "lucide-react";
import Header from "@/components/Header";
import { toolsApi, type ToolInfo } from "@/lib/api";

const MOCK_TOOLS: ToolInfo[] = [
  { slug: "web_scrape", name: "Web Scraper", description: "Fetch and extract content from any URL — text, links, metadata, or raw HTML.", category: "Web", icon: "🌐", is_builtin: true, requires_auth: false, parameters: { url: "string (required)", extract: "text|html|links|metadata" } },
  { slug: "web_search", name: "Web Search", description: "Search the web for information using DuckDuckGo. Returns top results with snippets.", category: "Web", icon: "🔍", is_builtin: true, requires_auth: false, parameters: { query: "string (required)", num_results: "integer (default 5)" } },
  { slug: "http_request", name: "HTTP Request", description: "Make GET/POST/PUT/DELETE requests to any REST API endpoint.", category: "API", icon: "📡", is_builtin: true, requires_auth: false, parameters: { method: "string", url: "string", headers: "dict", body: "dict" } },
  { slug: "parse_pdf", name: "PDF Parser", description: "Extract text content from PDF documents.", category: "Documents", icon: "📄", is_builtin: true, requires_auth: false, parameters: { file_path: "string (required)" } },
  { slug: "parse_docx", name: "Word Doc Parser", description: "Extract text from Microsoft Word (.docx) documents.", category: "Documents", icon: "📝", is_builtin: true, requires_auth: false, parameters: { file_path: "string (required)" } },
  { slug: "json_query", name: "JSON Query", description: "Query and extract values from JSON data using dot-notation paths.", category: "Data", icon: "🗄️", is_builtin: true, requires_auth: false, parameters: { data: "any", jq_path: "string" } },
  { slug: "calculator", name: "Calculator", description: "Safely evaluate mathematical expressions (+, -, *, /, **, %).", category: "Data", icon: "🧮", is_builtin: true, requires_auth: false, parameters: { expression: "string" } },
  { slug: "github_repo_info", name: "GitHub Info", description: "Fetch repository details, stats, and metadata from GitHub.", category: "Integrations", icon: "🐙", is_builtin: true, requires_auth: false, parameters: { owner: "string", repo: "string" } },
  { slug: "sql_query", name: "SQL Query", description: "Execute read-only SQL SELECT queries against SQLite databases.", category: "Data", icon: "🗃️", is_builtin: true, requires_auth: false, parameters: { connection_string: "string", query: "string" } },
  { slug: "extract_entities", name: "Entity Extractor", description: "Extract emails, URLs, dates, and numbers from unstructured text.", category: "NLP", icon: "🏷️", is_builtin: true, requires_auth: false, parameters: { text: "string" } },
  { slug: "summarize_text", name: "Text Summarizer", description: "Extract the most important sentences from a piece of text.", category: "NLP", icon: "📋", is_builtin: true, requires_auth: false, parameters: { text: "string", max_sentences: "integer" } },
  { slug: "translate", name: "Translator", description: "Translate text between languages.", category: "NLP", icon: "🌍", is_builtin: true, requires_auth: false, parameters: { text: "string", target_language: "string" } },
  { slug: "weather", name: "Weather", description: "Get current weather conditions for any location.", category: "Integrations", icon: "🌤️", is_builtin: true, requires_auth: false, parameters: { location: "string", units: "metric|imperial" } },
  { slug: "news_search", name: "News Search", description: "Search for recent news articles.", category: "Web", icon: "📰", is_builtin: true, requires_auth: false, parameters: { query: "string", category: "string" } },
  { slug: "send_slack", name: "Slack Message", description: "Send messages to Slack channels via webhook URL.", category: "Integrations", icon: "💬", is_builtin: true, requires_auth: true, parameters: { webhook_url: "string", message: "string" } },
];

const CATEGORY_COLORS: Record<string, string> = {
  Web: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  API: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  Documents: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  Data: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  NLP: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  Integrations: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
};

const DEMO_PARAMS: Record<string, Record<string, unknown>> = {
  web_search: { query: "AI agents 2025 trends", num_results: 3 },
  calculator: { expression: "2 ** 10 + 42" },
  extract_entities: { text: "Contact John Doe at john@example.com by March 15, 2025 for $1500." },
  summarize_text: { text: "Artificial intelligence is transforming industries across the globe. Companies are investing billions in AI research. Machine learning models are becoming more capable every year. The future of AI promises even greater advancements in healthcare, finance, and transportation.", max_sentences: 2 },
  weather: { location: "San Francisco, CA", units: "metric" },
  github_repo_info: { owner: "anthropics", repo: "anthropic-sdk-python" },
  translate: { text: "Hello, world!", target_language: "Spanish" },
  news_search: { query: "artificial intelligence", category: "technology" },
};

export default function ToolsPage() {
  const [tools, setTools] = useState<ToolInfo[]>(MOCK_TOOLS);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [executing, setExecuting] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, { success: boolean; output: unknown; error: string | null }>>({});
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    toolsApi.list().then((d) => setTools(d.tools)).catch(() => setTools(MOCK_TOOLS));
  }, []);

  const categories = ["All", ...Array.from(new Set(tools.map((t) => t.category)))];
  const filtered = tools.filter((t) => {
    const matchSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase());
    const matchCat = selectedCategory === "All" || t.category === selectedCategory;
    return matchSearch && matchCat;
  });

  const runTool = async (slug: string) => {
    const params = DEMO_PARAMS[slug] || {};
    setExecuting(slug);
    try {
      const res = await toolsApi.execute(slug, params);
      setResults((prev) => ({ ...prev, [slug]: res }));
      setExpanded(slug);
    } catch (e) {
      setResults((prev) => ({ ...prev, [slug]: { success: false, output: null, error: String(e) } }));
    } finally {
      setExecuting(null);
    }
  };

  return (
    <div className="animate-fade-in">
      <Header title="Tools" subtitle={`${tools.length} pre-built tool integrations — no setup required`} />

      <div className="p-6 space-y-5">
        {/* Search + filter */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 flex-1 min-w-[200px]">
            <Search size={15} className="text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tools..."
              className="flex-1 bg-transparent text-slate-300 text-sm outline-none placeholder-slate-600"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            {categories.map((cat) => (
              <button key={cat} onClick={() => setSelectedCategory(cat)}
                className={`text-xs px-3 py-2 rounded-lg border transition-all ${
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
          {filtered.map((tool) => {
            const catColor = CATEGORY_COLORS[tool.category] || "bg-slate-500/20 text-slate-400 border-slate-500/30";
            const res = results[tool.slug];
            const isExpanded = expanded === tool.slug;
            const canRun = !!DEMO_PARAMS[tool.slug];

            return (
              <div key={tool.slug} className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition-all">
                {/* Header */}
                <div className="flex items-start gap-3 mb-3">
                  <span className="text-2xl">{tool.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-white font-semibold text-sm">{tool.name}</h3>
                      {tool.requires_auth && (
                        <span className="text-xs bg-amber-900/30 text-amber-400 border border-amber-700/40 px-1.5 py-0.5 rounded">Auth</span>
                      )}
                    </div>
                    <span className={`text-xs border px-2 py-0.5 rounded-full mt-1 inline-block ${catColor}`}>
                      {tool.category}
                    </span>
                  </div>
                </div>

                <p className="text-slate-400 text-sm leading-relaxed mb-4">{tool.description}</p>

                {/* Params */}
                <div className="mb-4">
                  <div className="text-xs text-slate-600 mb-1.5">Parameters:</div>
                  <div className="space-y-1">
                    {Object.entries(tool.parameters).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-2 text-xs">
                        <code className="text-indigo-400 font-mono">{k}</code>
                        <span className="text-slate-600">—</span>
                        <span className="text-slate-500">{v as string}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {canRun && (
                    <button
                      onClick={() => runTool(tool.slug)}
                      disabled={executing === tool.slug}
                      className="flex items-center gap-1.5 text-xs bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 px-3 py-1.5 rounded-lg transition-all disabled:opacity-50"
                    >
                      {executing === tool.slug ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
                      Run Demo
                    </button>
                  )}
                  {res && (
                    <button onClick={() => setExpanded(isExpanded ? null : tool.slug)}
                      className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300">
                      {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                      Result
                    </button>
                  )}
                </div>

                {/* Result */}
                {res && isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-700 animate-fade-in">
                    <div className="flex items-center gap-2 mb-2">
                      {res.success
                        ? <CheckCircle size={14} className="text-emerald-400" />
                        : <XCircle size={14} className="text-red-400" />}
                      <span className={`text-xs font-medium ${res.success ? "text-emerald-400" : "text-red-400"}`}>
                        {res.success ? "Success" : "Error"}
                      </span>
                    </div>
                    <pre className="text-xs bg-slate-800 rounded-lg p-3 overflow-x-auto max-h-40 text-slate-300">
                      {JSON.stringify(res.output || res.error, null, 2)}
                    </pre>
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
