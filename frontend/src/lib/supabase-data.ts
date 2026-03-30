import { supabase } from "./supabase";
import type { AgentInfo, ToolInfo, LLMCard, RepoCard } from "./api";

export async function fetchAgents(): Promise<{ agents: AgentInfo[]; total: number; categories: string[] }> {
  const { data: agents, error } = await supabase
    .from("agents")
    .select("*")
    .eq("is_active", true);

  if (error || !agents) return { agents: [], total: 0, categories: [] };

  const mapped: AgentInfo[] = agents.map((a) => ({
    slug: a.slug,
    name: a.name,
    description: a.description || "",
    category: a.category || "",
    icon: a.icon || "🤖",
    capabilities: Array.isArray(a.capabilities) ? a.capabilities : [],
    required_tools: Array.isArray(a.required_tools) ? a.required_tools : [],
    preferred_llm: a.preferred_llm || "auto",
    is_builtin: a.is_builtin ?? false,
  }));

  const categories = [...new Set(mapped.map((a) => a.category).filter(Boolean))];
  return { agents: mapped, total: mapped.length, categories };
}

export async function fetchTools(): Promise<{ tools: ToolInfo[]; total: number; categories: string[] }> {
  const { data: tools, error: toolsErr } = await supabase
    .from("tools")
    .select("*")
    .eq("is_active", true);

  const { data: mcps, error: mcpsErr } = await supabase
    .from("mcps")
    .select("*")
    .eq("is_active", true);

  const allTools: ToolInfo[] = [];

  if (tools && !toolsErr) {
    for (const t of tools) {
      allTools.push({
        slug: t.slug,
        name: t.name,
        description: t.description || "",
        category: t.category || "",
        icon: t.icon || "🔧",
        is_builtin: t.is_builtin ?? false,
        requires_auth: t.requires_auth ?? false,
        parameters: typeof t.parameters_schema === "object" ? t.parameters_schema : {},
      });
    }
  }

  if (mcps && !mcpsErr) {
    for (const m of mcps) {
      allTools.push({
        slug: m.slug,
        name: m.name,
        description: m.description || "",
        category: m.source || "MCP",
        icon: "🛠️",
        is_builtin: false,
        requires_auth: true,
        parameters: { api_key: "Your API Key for this service" },
      });
    }
  }

  const categories = [...new Set(allTools.map((t) => t.category).filter(Boolean))];
  return { tools: allTools, total: allTools.length, categories };
}

export async function fetchLLMs(): Promise<{ llms: LLMCard[]; total: number }> {
  const { data: models, error } = await supabase
    .from("llm_models")
    .select("*")
    .eq("is_active", true)
    .order("cost_per_1m_input", { ascending: false })
    .limit(50);

  if (error || !models) return { llms: [], total: 0 };

  const bestForMap: Record<string, string[]> = {
    anthropic: ["Complex reasoning", "Code generation", "Research"],
    openai: ["Multimodal tasks", "Code generation", "Broad knowledge"],
    google: ["Long context", "Document analysis", "Multimodal"],
    "meta-llama": ["Open-weight", "Customizable", "Cost-efficient"],
    deepseek: ["Reasoning", "Chain-of-thought", "Cost-efficient"],
    mistralai: ["Multilingual", "Code generation", "Enterprise"],
    cohere: ["RAG", "Enterprise", "Tool use"],
    "x-ai": ["Real-time knowledge", "Analytics", "Broad tasks"],
    qwen: ["Multilingual", "Competitive reasoning", "Cost-efficient"],
  };

  const mapped: LLMCard[] = models.map((m) => ({
    id: m.id,
    display_name: m.display_name,
    provider: m.provider || "",
    description: m.description || "",
    best_for: bestForMap[m.provider] || ["General tasks"],
    pricing: {
      input_per_1m: m.cost_per_1m_input ?? 0,
      output_per_1m: m.cost_per_1m_output ?? 0,
    },
  }));

  return { llms: mapped, total: mapped.length };
}

export async function fetchRepos(): Promise<{ repos: RepoCard[]; total: number }> {
  const { data: repos, error } = await supabase
    .from("repos")
    .select("*")
    .order("stars", { ascending: false });

  if (error || !repos) return { repos: [], total: 0 };

  const mapped: RepoCard[] = repos.map((r) => ({
    name: r.name,
    full_name: r.full_name,
    description: r.description || "",
    stars: r.stars ?? 0,
    forks: r.forks ?? 0,
    url: r.url || "",
    language: r.language || "Mixed",
    topics: Array.isArray(r.topics) ? r.topics : [],
  }));

  return { repos: mapped, total: mapped.length };
}
