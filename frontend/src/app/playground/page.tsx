"use client";
import { useState, useRef, useCallback } from "react";
import {
  Send, Loader2, ChevronDown, ChevronUp,
  Cpu, Link2, X, Copy, Check, Info, Globe, Bot, Clock, DollarSign, Zap,
} from "lucide-react";
import Header from "@/components/Header";
import { API_BASE, getApiKey } from "@/lib/api";
import OrchestrationFlow, { type PipelineStep, type StepStatus } from "@/components/OrchestrationFlow";

const MODELS = [
  { id: "auto", label: "Auto (Recommended)", desc: "Gateway selects best model" },
  { id: "claude-opus-4-6", label: "Claude Opus 4.6", desc: "Most capable" },
  { id: "claude-sonnet-4-6", label: "Claude Sonnet 4.6", desc: "Balanced" },
  { id: "claude-haiku-4-5", label: "Claude Haiku 4.5", desc: "Fast & cheap" },
  { id: "gpt-4o", label: "GPT-4o", desc: "OpenAI flagship" },
  { id: "gemini-2.0-flash", label: "Gemini 2.0 Flash", desc: "Google model" },
];

const EXAMPLE_PROMPTS = [
  { label: "Research", prompt: "Research the latest trends in AI agents and summarize the key developments in 2025", icon: "🔬" },
  { label: "Code", prompt: "Write a Python FastAPI endpoint that accepts a file upload, extracts text from PDFs using PyPDF2, and returns the content as JSON", icon: "💻" },
  { label: "Analysis", prompt: "Analyze the business model of a SaaS company: key metrics to track, common failure points, and how to achieve product-market fit", icon: "📊" },
  { label: "Planning", prompt: "Create a 3-month roadmap for launching a B2B SaaS product including go-to-market strategy, tech stack decisions, and team hiring plan", icon: "🗺️" },
];

const MODEL_COLORS: Record<string, string> = {
  "claude-opus-4-6": "text-purple-400",
  "claude-sonnet-4-6": "text-blue-400",
  "claude-haiku-4-5-20251001": "text-emerald-400",
  "gpt-4o": "text-amber-400",
  "gemini-2.0-flash": "text-cyan-400",
};

// All steps that can appear, in order
const STEP_DEFS = [
  { id: "context",     label: "Extracting context" },
  { id: "intent",      label: "Analyzing intent" },
  { id: "llm_routing", label: "Routing to optimal LLM" },
  { id: "agents",      label: "Loading agents" },
  { id: "tools",       label: "Executing tools" },
  { id: "generation",  label: "Generating response" },
];

interface Metadata {
  task_category: string;
  complexity: string;
  selected_llm: string;
  selected_agents: string[];
  selected_tools: string[];
  tools_executed: Array<{ tool: string; success: boolean; output: unknown }>;
  context_extracted: boolean;
  routing_reason?: string;
}

interface Usage {
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="p-1.5 text-slate-400 hover:text-white rounded transition-colors"
    >
      {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
    </button>
  );
}

function MetaBadge({ icon: Icon, label, value, color = "text-slate-400" }: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string; value: string; color?: string;
}) {
  return (
    <div className="flex items-center gap-1.5 bg-slate-800 rounded-lg px-3 py-1.5">
      <Icon size={13} className={color} />
      <span className="text-slate-500 text-xs">{label}:</span>
      <span className={`text-xs font-medium ${color}`}>{value}</span>
    </div>
  );
}

function SDKSnippets({ prompt, model, contextUrl }: { prompt: string; model: string; contextUrl?: string }) {
  const [tab, setTab] = useState<"curl" | "python" | "js">("curl");
  const body = JSON.stringify({
    prompt: prompt.slice(0, 80) + (prompt.length > 80 ? "..." : ""),
    ...(model !== "auto" ? { preferred_model: model } : {}),
    ...(contextUrl ? { context_url: contextUrl } : {}),
  }, null, 2);

  const curl = `curl -X POST https://your-api.railway.app/v1/query \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '${body}'`;

  const python = `import requests

response = requests.post(
    "https://your-api.railway.app/v1/query",
    headers={"X-API-Key": "YOUR_API_KEY"},
    json=${body}
)
print(response.json()["response"])`;

  const js = `const res = await fetch("https://your-api.railway.app/v1/query", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "YOUR_API_KEY",
  },
  body: JSON.stringify(${body}),
});
const data = await res.json();
console.log(data.response);`;

  const code = tab === "curl" ? curl : tab === "python" ? python : js;

  return (
    <div className="border border-slate-700 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800/60 border-b border-slate-700">
        <span className="text-xs text-slate-400 font-medium">Reproduce via API</span>
        <div className="flex gap-1">
          {(["curl", "python", "js"] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${tab === t ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"}`}>
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="relative">
        <pre className="p-4 text-xs text-slate-300 font-mono overflow-x-auto bg-slate-900/60 leading-relaxed">{code}</pre>
        <div className="absolute top-2 right-2"><CopyButton text={code} /></div>
      </div>
    </div>
  );
}

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState("");
  const [contextUrl, setContextUrl] = useState("");
  const [model, setModel] = useState("auto");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showReason, setShowReason] = useState(false);
  const [showSdk, setShowSdk] = useState(false);

  const [streaming, setStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Pipeline flow state
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([]);

  const abortRef = useRef<AbortController | null>(null);

  const updateStep = useCallback((stepId: string, status: StepStatus, label?: string, details?: Record<string, unknown>) => {
    setPipelineSteps(prev => {
      const existing = prev.find(s => s.id === stepId);
      if (existing) {
        return prev.map(s => s.id === stepId ? { ...s, status, ...(label ? { label } : {}), ...(details ? { details } : {}) } : s);
      }
      return [...prev, { id: stepId, label: label || stepId, status, details }];
    });
  }, []);

  const submit = useCallback(async () => {
    if (!prompt.trim() || streaming) return;
    setStreaming(true);
    setStreamedText("");
    setMetadata(null);
    setUsage(null);
    setError(null);
    setShowReason(false);
    setShowSdk(false);

    // Initialize pipeline with known steps (skip context if no URL)
    const initialSteps: PipelineStep[] = STEP_DEFS
      .filter(s => s.id !== "context" || contextUrl.trim())
      .map(s => ({ id: s.id, label: s.label, status: "pending" as StepStatus }));
    setPipelineSteps(initialSteps);

    abortRef.current = new AbortController();

    try {
      const body: Record<string, unknown> = { prompt };
      if (model !== "auto") body.preferred_model = model;
      if (contextUrl.trim()) body.context_url = contextUrl.trim();

      const res = await fetch(`${API_BASE}/v1/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": getApiKey() },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6);
          if (raw === "[DONE]") { setStreaming(false); break; }

          try {
            const event = JSON.parse(raw);

            if (event.type === "step_start") {
              updateStep(event.step, "active", event.label);
            } else if (event.type === "step_complete") {
              updateStep(event.step, "complete", event.label, event.details);
            } else if (event.type === "token") {
              setStreamedText(prev => prev + event.text);
            } else if (event.type === "metadata") {
              setMetadata(event);
            } else if (event.type === "done") {
              setUsage({
                input_tokens: event.input_tokens,
                output_tokens: event.output_tokens,
                cost_usd: event.cost_usd,
                latency_ms: event.latency_ms,
              });
              setStreaming(false);
            } else if (event.type === "error") {
              throw new Error(event.detail);
            }
          } catch (parseErr) {
            if (parseErr instanceof SyntaxError) continue;
            throw parseErr;
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== "AbortError") setError(e.message);
      setStreaming(false);
    }
  }, [prompt, model, contextUrl, streaming, updateStep]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
  };

  const hasResult = streamedText.length > 0;
  const hasFlow = pipelineSteps.length > 0;

  return (
    <div className="flex flex-col gap-6 p-6 max-w-5xl mx-auto">
      <Header title="Playground" subtitle="Type any task — watch the gateway route it in real time" />

      {/* Example prompts */}
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map(p => (
          <button key={p.label} onClick={() => setPrompt(p.prompt)}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm text-slate-300 transition-colors">
            <span>{p.icon}</span><span>{p.label}</span>
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden focus-within:border-indigo-500 transition-colors">
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything — the gateway will route to the right LLM, agents, and tools automatically..."
          rows={5}
          className="w-full bg-transparent p-4 text-white placeholder-slate-500 resize-none outline-none text-sm leading-relaxed"
        />

        <div className="border-t border-slate-800 px-4 py-3">
          <button onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 text-slate-400 hover:text-white text-xs transition-colors">
            {showAdvanced ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            Advanced options
          </button>
          {showAdvanced && (
            <div className="mt-3 flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <Link2 size={14} className="text-slate-500 shrink-0" />
                <input value={contextUrl} onChange={e => setContextUrl(e.target.value)}
                  placeholder="Context URL (optional — scrapes page content automatically)"
                  className="flex-1 bg-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 outline-none border border-slate-700 focus:border-indigo-500 transition-colors" />
              </div>
              <div className="flex items-center gap-3">
                <Cpu size={14} className="text-slate-500 shrink-0" />
                <select value={model} onChange={e => setModel(e.target.value)}
                  className="flex-1 bg-slate-800 rounded-lg px-3 py-2 text-sm text-white outline-none border border-slate-700 focus:border-indigo-500 transition-colors">
                  {MODELS.map(m => (
                    <option key={m.id} value={m.id}>{m.label} — {m.desc}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-slate-800 px-4 py-3 flex items-center justify-between">
          <span className="text-xs text-slate-600">⌘ + Enter to submit</span>
          <div className="flex gap-2">
            {streaming && (
              <button onClick={() => abortRef.current?.abort()}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-slate-300 transition-colors">
                <X size={13} /> Stop
              </button>
            )}
            <button onClick={submit} disabled={!prompt.trim() || streaming}
              className="flex items-center gap-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm text-white font-medium transition-colors">
              {streaming ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
              {streaming ? "Running..." : "Submit"}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 text-red-400 text-sm">{error}</div>
      )}

      {/* Two-column layout: pipeline flow + response */}
      {hasFlow && (
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 items-start">

          {/* LEFT: Live orchestration pipeline */}
          <OrchestrationFlow steps={pipelineSteps} />

          {/* RIGHT: Response + metadata */}
          <div className="flex flex-col gap-4">

            {/* Meta badges (appear once metadata arrives) */}
            {metadata && (
              <div className="flex flex-wrap gap-2">
                <MetaBadge icon={Cpu} label="LLM" value={metadata.selected_llm}
                  color={MODEL_COLORS[metadata.selected_llm] || "text-slate-300"} />
                <MetaBadge icon={Zap} label="Category" value={metadata.task_category} color="text-indigo-400" />
                {usage && <MetaBadge icon={Clock} label="Latency" value={`${usage.latency_ms}ms`} color="text-amber-400" />}
                {usage && <MetaBadge icon={DollarSign} label="Cost" value={`$${usage.cost_usd.toFixed(5)}`} color="text-emerald-400" />}
                {metadata.selected_agents.length > 0 && (
                  <MetaBadge icon={Bot} label="Agents" value={metadata.selected_agents.join(", ")} />
                )}
                {metadata.context_extracted && (
                  <MetaBadge icon={Globe} label="Context" value="Extracted" color="text-cyan-400" />
                )}
              </div>
            )}

            {/* Why this routing */}
            {metadata?.routing_reason && (
              <div className="border border-slate-800 rounded-xl overflow-hidden">
                <button onClick={() => setShowReason(!showReason)}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-900 hover:bg-slate-800/60 transition-colors text-left">
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <Info size={13} className="text-indigo-400" />
                    Why this routing?
                  </div>
                  {showReason ? <ChevronUp size={13} className="text-slate-500" /> : <ChevronDown size={13} className="text-slate-500" />}
                </button>
                {showReason && (
                  <div className="px-4 py-3 bg-slate-900/40 text-xs text-slate-400 leading-relaxed border-t border-slate-800">
                    {metadata.routing_reason}
                  </div>
                )}
              </div>
            )}

            {/* Response text */}
            {(hasResult || streaming) && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800">
                  <span className="text-xs text-slate-500 font-medium">Response</span>
                  {hasResult && <CopyButton text={streamedText} />}
                </div>
                <div className="p-4 text-sm text-slate-200 leading-relaxed whitespace-pre-wrap min-h-[80px]">
                  {streamedText || (
                    <span className="text-slate-600 italic text-xs">Waiting for response...</span>
                  )}
                  {streaming && streamedText && (
                    <span className="inline-block w-2 h-4 bg-indigo-400 animate-pulse ml-0.5 align-middle" />
                  )}
                </div>
              </div>
            )}

            {/* Usage */}
            {usage && (
              <div className="flex gap-4 text-xs text-slate-500">
                <span>{usage.input_tokens.toLocaleString()} input tokens</span>
                <span>·</span>
                <span>{usage.output_tokens.toLocaleString()} output tokens</span>
                <span>·</span>
                <span className="text-emerald-500">${usage.cost_usd.toFixed(6)} total cost</span>
              </div>
            )}

            {/* SDK Snippets */}
            {hasResult && (
              <>
                <button onClick={() => setShowSdk(!showSdk)}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-400 transition-colors w-fit">
                  {showSdk ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  {showSdk ? "Hide" : "Show"} API code to reproduce this
                </button>
                {showSdk && <SDKSnippets prompt={prompt} model={model} contextUrl={contextUrl || undefined} />}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
