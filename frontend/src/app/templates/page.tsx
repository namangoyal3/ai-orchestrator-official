"use client";
import { useState } from "react";
import Header from "@/components/Header";
import {
  LayoutTemplate, Search, Zap, Globe, Database, Shield, CreditCard,
  Mail, Brain, Bot, Wrench, Copy, Check, ExternalLink, Star,
  ShoppingCart, HeadphonesIcon, BarChart2, MessageSquare, FileText,
  Rocket, Code2, Users,
} from "lucide-react";
import clsx from "clsx";

interface TemplateStack {
  name: string;
  category: string;
  tier: "free" | "freemium" | "paid";
}

interface TemplateAgent {
  name: string;
  icon: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  iconColor: string;
  tags: string[];
  stack: TemplateStack[];
  agents: TemplateAgent[];
  tools: string[];
  stars: number;
  source: "community" | "official";
}

const TEMPLATES: Template[] = [
  {
    id: "ai-customer-support",
    name: "AI Customer Support Platform",
    description:
      "Multi-tenant support platform with chat, email, and WhatsApp. Auto-resolves order tracking and refunds, escalates complex issues to human agents with full context.",
    category: "SaaS",
    icon: HeadphonesIcon,
    iconColor: "text-violet-400",
    tags: ["multi-tenant", "WhatsApp", "AI escalation", "e-commerce"],
    stack: [
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "Next.js",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Redis",      category: "cache",    tier: "free" },
      { name: "Twilio",     category: "notifications", tier: "paid" },
      { name: "Resend",     category: "email",    tier: "freemium" },
    ],
    agents: [
      { name: "customer_support", icon: "🎧" },
      { name: "document_qa",      icon: "📄" },
      { name: "planning",         icon: "🗺️" },
    ],
    tools: ["web_search", "web_scrape", "pdf_parser"],
    stars: 142,
    source: "official",
  },
  {
    id: "competitive-intelligence",
    name: "Competitive Intelligence Monitor",
    description:
      "Monitors competitor websites, pricing pages, and changelogs in real-time. Sends weekly Slack/email digests with actionable insights and trend analysis.",
    category: "B2B SaaS",
    icon: BarChart2,
    iconColor: "text-blue-400",
    tags: ["competitor tracking", "scraping", "digests", "analytics"],
    stack: [
      { name: "Next.js",    category: "web",      tier: "free" },
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Redis",      category: "cache",    tier: "free" },
      { name: "Celery",     category: "queue",    tier: "free" },
      { name: "Resend",     category: "email",    tier: "freemium" },
    ],
    agents: [
      { name: "research",       icon: "🔍" },
      { name: "content_writer", icon: "✍️" },
      { name: "data_analysis",  icon: "📊" },
    ],
    tools: ["web_search", "web_scrape"],
    stars: 98,
    source: "official",
  },
  {
    id: "saas-starter",
    name: "SaaS Starter Kit",
    description:
      "Full-stack SaaS boilerplate with auth, billing, teams, and admin. Ships with Stripe subscriptions, role-based access, and a React dashboard out of the box.",
    category: "SaaS",
    icon: Rocket,
    iconColor: "text-emerald-400",
    tags: ["auth", "billing", "teams", "admin"],
    stack: [
      { name: "Next.js",    category: "web",      tier: "free" },
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Clerk",      category: "auth",     tier: "freemium" },
      { name: "Stripe",     category: "payments", tier: "paid" },
      { name: "Resend",     category: "email",    tier: "freemium" },
    ],
    agents: [],
    tools: [],
    stars: 311,
    source: "official",
  },
  {
    id: "ai-research-assistant",
    name: "AI Research Assistant",
    description:
      "Deep research tool that searches the web, scrapes sources, synthesizes findings, and generates structured reports — with citations. Built for analysts and founders.",
    category: "AI Tool",
    icon: Brain,
    iconColor: "text-purple-400",
    tags: ["research", "web search", "reports", "RAG"],
    stack: [
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "Next.js",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Supabase",   category: "database", tier: "freemium" },
    ],
    agents: [
      { name: "research",      icon: "🔍" },
      { name: "document_qa",   icon: "📄" },
      { name: "data_analysis", icon: "📊" },
    ],
    tools: ["web_search", "web_scrape", "pdf_parser"],
    stars: 204,
    source: "official",
  },
  {
    id: "ecommerce-ai",
    name: "AI-Powered E-commerce Store",
    description:
      "Full e-commerce platform with AI product recommendations, smart search, and automated inventory alerts. Includes Razorpay/Stripe checkout and order management.",
    category: "E-commerce",
    icon: ShoppingCart,
    iconColor: "text-orange-400",
    tags: ["recommendations", "payments", "inventory", "search"],
    stack: [
      { name: "Next.js",    category: "web",      tier: "free" },
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Redis",      category: "cache",    tier: "free" },
      { name: "Stripe",     category: "payments", tier: "paid" },
      { name: "Razorpay",   category: "payments", tier: "paid" },
    ],
    agents: [
      { name: "research",        icon: "🔍" },
      { name: "customer_support", icon: "🎧" },
    ],
    tools: ["web_search"],
    stars: 187,
    source: "official",
  },
  {
    id: "doc-qa-platform",
    name: "Document Q&A Platform",
    description:
      "Upload PDFs, contracts, or knowledge bases and ask questions in natural language. Supports multi-doc context, source citations, and team sharing.",
    category: "AI Tool",
    icon: FileText,
    iconColor: "text-sky-400",
    tags: ["RAG", "PDF", "Q&A", "knowledge base"],
    stack: [
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "Next.js",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Supabase",   category: "database", tier: "freemium" },
    ],
    agents: [
      { name: "document_qa", icon: "📄" },
      { name: "research",    icon: "🔍" },
    ],
    tools: ["pdf_parser", "web_search"],
    stars: 167,
    source: "community",
  },
  {
    id: "ai-code-reviewer",
    name: "AI Code Review Bot",
    description:
      "GitHub-integrated bot that reviews PRs, suggests improvements, flags security issues, and enforces code style — powered by Claude. Works across any language.",
    category: "DevTools",
    icon: Code2,
    iconColor: "text-yellow-400",
    tags: ["GitHub", "code review", "security", "DevTools"],
    stack: [
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Redis",      category: "cache",    tier: "free" },
      { name: "Docker",     category: "deploy",   tier: "free" },
    ],
    agents: [
      { name: "code",     icon: "💻" },
      { name: "research", icon: "🔍" },
    ],
    tools: ["web_search"],
    stars: 129,
    source: "community",
  },
  {
    id: "community-platform",
    name: "Community & Forum Platform",
    description:
      "Modern community platform with AI-powered moderation, thread summarization, and smart notifications. Think Discord meets Notion with an AI layer.",
    category: "Consumer",
    icon: Users,
    iconColor: "text-pink-400",
    tags: ["community", "moderation", "notifications", "social"],
    stack: [
      { name: "Next.js",    category: "web",      tier: "free" },
      { name: "FastAPI",    category: "web",      tier: "free" },
      { name: "PostgreSQL", category: "database", tier: "free" },
      { name: "Redis",      category: "cache",    tier: "free" },
      { name: "Supabase",   category: "database", tier: "freemium" },
      { name: "Firebase FCM", category: "notifications", tier: "freemium" },
    ],
    agents: [
      { name: "content_writer", icon: "✍️" },
      { name: "planning",       icon: "🗺️" },
    ],
    tools: ["web_search"],
    stars: 93,
    source: "community",
  },
];

const CATEGORIES = ["All", "SaaS", "B2B SaaS", "AI Tool", "E-commerce", "DevTools", "Consumer"];

const TIER_COLOR: Record<string, string> = {
  free:      "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  freemium:  "text-sky-400 bg-sky-400/10 border-sky-400/20",
  paid:      "text-amber-400 bg-amber-400/10 border-amber-400/20",
};

function TemplateBadge({ label, color }: { label: string; color?: string }) {
  return (
    <span className={clsx(
      "text-[10px] px-2 py-0.5 rounded-full border font-medium",
      color ?? "text-zinc-400 bg-white/[0.05] border-white/[0.08]"
    )}>
      {label}
    </span>
  );
}

function TemplateCard({ tpl, onUse }: { tpl: Template; onUse: (t: Template) => void }) {
  const Icon = tpl.icon;
  return (
    <div className="bg-[#18181b] border border-white/[0.07] rounded-xl p-5 flex flex-col gap-4 hover:border-white/[0.14] transition-colors group">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-white/[0.05] border border-white/[0.07] flex items-center justify-center shrink-0">
            <Icon size={17} className={tpl.iconColor} />
          </div>
          <div>
            <h3 className="text-[13px] font-semibold text-white leading-tight">{tpl.name}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <TemplateBadge
                label={tpl.source === "official" ? "Official" : "Community"}
                color={tpl.source === "official"
                  ? "text-brand-300 bg-brand-500/10 border-brand-400/20"
                  : "text-zinc-400 bg-white/[0.05] border-white/[0.08]"}
              />
              <TemplateBadge label={tpl.category} />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 text-zinc-500 text-[11px] shrink-0">
          <Star size={11} className="text-amber-400" />
          <span>{tpl.stars}</span>
        </div>
      </div>

      {/* Description */}
      <p className="text-zinc-400 text-[12px] leading-relaxed">{tpl.description}</p>

      {/* Tags */}
      <div className="flex flex-wrap gap-1">
        {tpl.tags.map(tag => (
          <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-zinc-500 border border-white/[0.06]">
            {tag}
          </span>
        ))}
      </div>

      {/* Stack pills */}
      <div>
        <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest mb-1.5">Stack</p>
        <div className="flex flex-wrap gap-1.5">
          {tpl.stack.map(s => (
            <span key={s.name} className={clsx(
              "text-[10px] px-2 py-0.5 rounded-full border font-medium",
              TIER_COLOR[s.tier]
            )}>
              {s.name}
            </span>
          ))}
        </div>
      </div>

      {/* Agents + Tools */}
      {(tpl.agents.length > 0 || tpl.tools.length > 0) && (
        <div>
          <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest mb-1.5">AI Layer</p>
          <div className="flex flex-wrap gap-1.5">
            {tpl.agents.map(a => (
              <span key={a.name} className="text-[10px] px-2 py-0.5 rounded-full border text-violet-300 bg-violet-400/10 border-violet-400/20 font-medium">
                {a.icon} {a.name}
              </span>
            ))}
            {tpl.tools.map(t => (
              <span key={t} className="text-[10px] px-2 py-0.5 rounded-full border text-sky-300 bg-sky-400/10 border-sky-400/20 font-medium">
                🔧 {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 mt-auto">
        <button
          onClick={() => onUse(tpl)}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-[12px] font-semibold transition-colors"
        >
          <Zap size={12} />
          Use Template
        </button>
        <button className="px-3 py-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.07] border border-white/[0.08] text-zinc-400 hover:text-zinc-200 text-[12px] transition-colors">
          <ExternalLink size={13} />
        </button>
      </div>
    </div>
  );
}

function CopiedSnippet({ tpl }: { tpl: Template }) {
  const [copied, setCopied] = useState(false);
  const cmd = `namango init "${tpl.name.toLowerCase().replace(/ /g, '-')}"`;

  const copy = () => {
    navigator.clipboard.writeText(cmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center gap-2 mt-3 bg-black/40 rounded-lg px-3 py-2 border border-white/[0.08] font-mono text-[11px]">
      <span className="text-zinc-500 select-none">$</span>
      <span className="text-emerald-300 flex-1">{cmd}</span>
      <button onClick={copy} className="text-zinc-500 hover:text-zinc-200 transition-colors">
        {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
      </button>
    </div>
  );
}

export default function TemplatesPage() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [selectedTpl, setSelectedTpl] = useState<Template | null>(null);

  const filtered = TEMPLATES.filter(t => {
    const matchCat = activeCategory === "All" || t.category === activeCategory;
    const q = search.toLowerCase();
    const matchSearch = !q || t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) || t.tags.some(g => g.toLowerCase().includes(q));
    return matchCat && matchSearch;
  });

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header
        title="Templates"
        subtitle="Production-ready MVP stacks — pick one and start building"
        icon={<LayoutTemplate size={18} className="text-brand-400" />}
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Search + filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search templates…"
              className="w-full pl-8 pr-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-[13px] text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/30"
            />
          </div>
          <div className="flex gap-1.5 flex-wrap">
            {CATEGORIES.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={clsx(
                  "px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors border",
                  activeCategory === cat
                    ? "bg-brand-600/20 text-brand-300 border-brand-500/40"
                    : "bg-white/[0.03] text-zinc-400 border-white/[0.07] hover:text-zinc-200 hover:border-white/[0.12]"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-4 text-[11px] text-zinc-500">
          <span>{filtered.length} template{filtered.length !== 1 ? "s" : ""}</span>
          <span>·</span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-brand-500" />
            Official
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-zinc-600" />
            Community
          </span>
        </div>

        {/* Grid */}
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <LayoutTemplate size={32} className="text-zinc-700 mb-3" />
            <p className="text-zinc-400 font-medium">No templates match your search</p>
            <p className="text-zinc-600 text-[12px] mt-1">Try a different keyword or category</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map(tpl => (
              <TemplateCard key={tpl.id} tpl={tpl} onUse={setSelectedTpl} />
            ))}
          </div>
        )}

        {/* Submit CTA */}
        <div className="border border-dashed border-white/[0.08] rounded-xl p-6 text-center bg-white/[0.01]">
          <p className="text-zinc-400 text-[13px] font-medium">Built something worth sharing?</p>
          <p className="text-zinc-600 text-[12px] mt-1 mb-3">
            Submit your stack as a community template — built by the CLI, saved here for everyone.
          </p>
          <button className="px-4 py-2 bg-white/[0.05] hover:bg-white/[0.08] border border-white/[0.1] rounded-lg text-zinc-300 text-[12px] font-medium transition-colors">
            + Submit a Template
          </button>
        </div>
      </div>

      {/* Use Template Modal */}
      {selectedTpl && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedTpl(null)}
        >
          <div
            className="bg-[#18181b] border border-white/[0.1] rounded-2xl p-6 max-w-md w-full shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                <selectedTpl.icon size={19} className={selectedTpl.iconColor} />
              </div>
              <div>
                <h3 className="text-white font-semibold text-[14px]">{selectedTpl.name}</h3>
                <p className="text-zinc-500 text-[11px]">{selectedTpl.stack.length} tools · {selectedTpl.agents.length} agents</p>
              </div>
            </div>
            <p className="text-zinc-400 text-[12px] leading-relaxed mb-4">{selectedTpl.description}</p>
            <div>
              <p className="text-zinc-500 text-[11px] mb-1">Run this in your terminal to scaffold the project:</p>
              <CopiedSnippet tpl={selectedTpl} />
            </div>
            <button
              onClick={() => setSelectedTpl(null)}
              className="mt-4 w-full py-2 rounded-lg bg-white/[0.05] hover:bg-white/[0.08] text-zinc-400 text-[12px] transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
