"use client";
import Link from "next/link";
import { useState } from "react";
import {
  Zap, ArrowRight, Terminal, Globe, Shield, BarChart2,
  Bot, Layers, Check, Copy, ChevronRight, ExternalLink,
} from "lucide-react";

const FEATURES = [
  {
    icon: Zap,
    title: "Smart LLM Routing",
    description: "Automatically selects the optimal model — Claude, GPT-4, Gemini — based on task type, cost, and latency.",
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
  },
  {
    icon: Bot,
    title: "Agent Marketplace",
    description: "108+ pre-configured agents for research, coding, data analysis, and content creation. Deploy in seconds.",
    color: "text-purple-400",
    bg: "bg-purple-400/10",
  },
  {
    icon: Layers,
    title: "Stack Recommender",
    description: "Describe your product. Get a curated set of tools, APIs, and services matched to your exact needs.",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
  {
    icon: BarChart2,
    title: "Real-time Analytics",
    description: "Track request volume, success rates, token costs, and model usage across all providers.",
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
  },
  {
    icon: Shield,
    title: "API Key Management",
    description: "Org-scoped API keys with fine-grained permissions, expiry, and usage tracking.",
    color: "text-red-400",
    bg: "bg-red-400/10",
  },
  {
    icon: Globe,
    title: "Universal Compatibility",
    description: "Single REST API with OpenAI-compatible format. Drop-in replacement for any LLM provider.",
    color: "text-cyan-400",
    bg: "bg-cyan-400/10",
  },
];

const PRICING = [
  {
    name: "Starter",
    price: "Free",
    period: "",
    description: "For personal projects and exploration.",
    features: ["10K requests/month", "3 agents", "All LLM providers", "Community support"],
    cta: "Get started",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For teams shipping real products.",
    features: ["500K requests/month", "All 108+ agents", "Stack recommender", "Priority routing", "Analytics dashboard", "Email support"],
    cta: "Start free trial",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For production workloads at scale.",
    features: ["Unlimited requests", "Custom agents", "SLA guarantee", "SSO + SAML", "Dedicated support", "On-premise option"],
    cta: "Contact us",
    highlight: false,
  },
];

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1800); }}
      className="p-1.5 text-zinc-500 hover:text-zinc-200 transition-colors"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 font-sans">

      {/* Nav */}
      <nav className="border-b border-white/[0.06] sticky top-0 bg-[#09090b]/80 backdrop-blur-md z-50">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-900/50">
              <Zap size={13} className="text-white" />
            </div>
            <span className="font-semibold text-white text-[14px]">AI Gateway</span>
          </div>
          <div className="flex items-center gap-1">
            <Link href="/docs" className="px-3 py-1.5 text-zinc-400 hover:text-white text-[13px] transition-colors">Docs</Link>
            <Link href="/marketplace" className="px-3 py-1.5 text-zinc-400 hover:text-white text-[13px] transition-colors">Marketplace</Link>
            <Link href="/analytics" className="px-3 py-1.5 text-zinc-400 hover:text-white text-[13px] transition-colors">Pricing</Link>
            <Link href="/"
              className="ml-2 px-3.5 py-1.5 bg-brand-600 hover:bg-brand-500 text-white text-[13px] font-medium rounded-lg transition-colors flex items-center gap-1.5">
              Open App <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-dark bg-[size:32px_32px] opacity-100" />
        <div className="absolute inset-0 bg-gradient-to-b from-brand-950/30 via-transparent to-[#09090b]" />
        <div className="relative max-w-4xl mx-auto px-6 pt-24 pb-20 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-brand-500/25 bg-brand-500/10 text-brand-300 text-[12px] font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            v1.1.0 · Stack recommender now live
            <ChevronRight size={12} className="text-brand-400" />
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold text-white leading-[1.1] tracking-tight mb-6">
            Universal AI<br />
            <span className="text-gradient">infrastructure</span>
          </h1>
          <p className="text-zinc-400 text-lg leading-relaxed max-w-2xl mx-auto mb-10">
            Route any task to the optimal LLM. Access 108+ pre-built agents.
            Get AI-powered stack recommendations. One API, every provider.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/"
              className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-medium rounded-lg transition-colors flex items-center gap-2 text-[14px]">
              Open Dashboard <ArrowRight size={15} />
            </Link>
            <div className="flex items-center gap-2 bg-[#111113] border border-white/[0.08] rounded-lg px-4 py-2.5 font-mono text-[13px] text-zinc-400">
              <span className="text-zinc-600">$</span>
              <span>pip install namango</span>
              <CopyBtn text="pip install namango" />
            </div>
          </div>
          <p className="text-zinc-600 text-[12px] mt-6">Free tier available · No credit card required</p>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold text-white mb-3">Everything AI needs, out of the box</h2>
          <p className="text-zinc-500 text-[15px]">From routing to agents to analytics — one platform for your entire AI stack.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map(f => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="p-5 rounded-xl border border-white/[0.07] bg-[#111113] hover:border-white/[0.12] transition-colors">
                <div className={`w-9 h-9 rounded-lg ${f.bg} flex items-center justify-center mb-4`}>
                  <Icon size={17} className={f.color} />
                </div>
                <h3 className="text-white font-semibold text-[14px] mb-2">{f.title}</h3>
                <p className="text-zinc-500 text-[13px] leading-relaxed">{f.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Code example */}
      <section className="max-w-6xl mx-auto px-6 py-10 pb-20">
        <div className="rounded-2xl border border-white/[0.08] bg-[#111113] overflow-hidden">
          <div className="border-b border-white/[0.06] px-5 py-3.5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-brand-400" />
              <span className="text-[13px] font-medium text-white">Quick start</span>
            </div>
            <span className="text-[11px] text-zinc-600">Python · JavaScript · CLI</span>
          </div>
          <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/[0.05]">
            <div className="p-5">
              <p className="text-[11px] text-zinc-600 uppercase tracking-widest font-medium mb-3">CLI</p>
              <pre className="text-[12.5px] leading-loose bg-transparent border-0 p-0 text-zinc-300"><code>{`# Install the CLI
pip install namango

# Initialize your project
namango init

# Get AI stack recommendations
namango recommend "B2B SaaS analytics tool"

# Browse 58 curated tools
namango stacks`}</code></pre>
            </div>
            <div className="p-5">
              <p className="text-[11px] text-zinc-600 uppercase tracking-widest font-medium mb-3">API</p>
              <pre className="text-[12.5px] leading-loose bg-transparent border-0 p-0 text-zinc-300"><code>{`import httpx

response = httpx.post(
  "https://api.namango.ai/v1/query",
  headers={"X-API-Key": "gw-..."},
  json={
    "task": "Analyze this dataset",
    "category": "analysis",
  }
)
print(response.json())`}</code></pre>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-5xl mx-auto px-6 py-10 pb-24">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold text-white mb-3">Simple pricing</h2>
          <p className="text-zinc-500 text-[15px]">Start free, scale when you need it.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PRICING.map(plan => (
            <div key={plan.name} className={`rounded-xl border p-6 flex flex-col ${
              plan.highlight
                ? "border-brand-500/40 bg-brand-500/[0.06]"
                : "border-white/[0.07] bg-[#111113]"
            }`}>
              {plan.highlight && (
                <div className="badge badge-indigo w-fit mb-3 text-[10px]">Most popular</div>
              )}
              <div className="mb-1">
                <span className="text-2xl font-bold text-white">{plan.price}</span>
                <span className="text-zinc-500 text-[13px]">{plan.period}</span>
              </div>
              <p className="text-[13px] font-medium text-white mb-1">{plan.name}</p>
              <p className="text-zinc-500 text-[12px] mb-5">{plan.description}</p>
              <ul className="space-y-2.5 mb-6 flex-1">
                {plan.features.map(f => (
                  <li key={f} className="flex items-center gap-2 text-[13px] text-zinc-400">
                    <Check size={13} className={plan.highlight ? "text-brand-400" : "text-emerald-400"} />
                    {f}
                  </li>
                ))}
              </ul>
              <Link href="/"
                className={`w-full py-2 rounded-lg text-[13px] font-medium text-center transition-colors ${
                  plan.highlight
                    ? "bg-brand-600 hover:bg-brand-500 text-white"
                    : "bg-white/[0.05] hover:bg-white/[0.09] text-zinc-300 border border-white/[0.08]"
                }`}>
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[12px] text-zinc-600">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
              <Zap size={10} className="text-white" />
            </div>
            <span>AI Gateway · Universal LLM Orchestration</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://github.com/namangoyal3/ai-orchestrator-official" target="_blank" rel="noopener noreferrer"
              className="hover:text-zinc-400 transition-colors flex items-center gap-1">
              GitHub <ExternalLink size={10} />
            </a>
            <Link href="/" className="hover:text-zinc-400 transition-colors">Dashboard</Link>
            <Link href="/marketplace" className="hover:text-zinc-400 transition-colors">Marketplace</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
