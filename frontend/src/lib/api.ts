export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://ai-gateway-backend-production.up.railway.app";
const DEMO_KEY = "gw-demo-key-change-in-production-12345678";

export function getApiKey(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("gw_api_key") || DEMO_KEY;
  }
  return DEMO_KEY;
}

export function setApiKey(key: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("gw_api_key", key);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": getApiKey(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ─── Gateway ───────────────────────────────────

export interface QueryRequest {
  prompt: string;
  context_url?: string;
  context_text?: string;
  preferred_model?: string;
  preferred_agents?: string[];
  preferred_tools?: string[];
  max_tokens?: number;
}

export interface GatewayResponse {
  id: string;
  response: string;
  orchestration: {
    task_category: string;
    complexity: string;
    selected_llm: string;
    selected_agents: string[];
    selected_tools: string[];
    tools_executed: Array<{ tool: string; success: boolean; output: unknown }>;
    context_extracted: boolean;
    routing_reason: string;
  };
  usage: {
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    latency_ms: number;
  };
  created_at: string;
}

export const gateway = {
  query: (body: QueryRequest) =>
    request<GatewayResponse>("/v1/query", { method: "POST", body: JSON.stringify(body) }),
  models: () => request<{ models: ModelInfo[] }>("/v1/models"),
  history: (limit = 20) => request<{ items: HistoryItem[]; total: number }>(`/v1/history?limit=${limit}`),
};

// ─── Agents ────────────────────────────────────

export interface AgentInfo {
  slug: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  capabilities: string[];
  required_tools: string[];
  preferred_llm: string;
  is_builtin: boolean;
}

export const agentsApi = {
  list: () => request<{ agents: AgentInfo[]; total: number }>("/v1/agents"),
  get: (slug: string) => request<AgentInfo>(`/v1/agents/${slug}`),
};

// ─── Tools ─────────────────────────────────────

export interface ToolInfo {
  slug: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  is_builtin: boolean;
  requires_auth: boolean;
  parameters: Record<string, string>;
}

export const toolsApi = {
  list: () => request<{ tools: ToolInfo[]; total: number; categories: string[] }>("/v1/tools"),
  execute: (slug: string, params: Record<string, unknown>) =>
    request<{ tool: string; success: boolean; output: unknown; error: string | null }>(
      `/v1/tools/${slug}/execute`,
      { method: "POST", body: JSON.stringify({ params }) }
    ),
};

// ─── Analytics ─────────────────────────────────

export interface AnalyticsSummary {
  period_days: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
}

export interface TimelinePoint {
  date: string;
  requests: number;
  cost: number;
}

export const analyticsApi = {
  summary: (days = 30) => request<AnalyticsSummary>(`/v1/analytics/summary?days=${days}`),
  timeseries: (days = 14) => request<{ timeline: TimelinePoint[] }>(`/v1/analytics/timeseries?days=${days}`),
  models: (days = 30) => request<{ models: Array<{ model: string; requests: number; cost: number }> }>(`/v1/analytics/models?days=${days}`),
  categories: (days = 30) => request<{ categories: Array<{ category: string; requests: number }> }>(`/v1/analytics/categories?days=${days}`),
};

// ─── Admin ─────────────────────────────────────

export interface ModelInfo {
  id: string;
  display_name: string;
  provider: string;
  description: string;
  pricing: { input_per_1m: number; output_per_1m: number };
}

export interface HistoryItem {
  id: string;
  prompt: string;
  status: string;
  selected_llm: string;
  selected_agents: string[];
  task_category: string;
  latency_ms: number;
  cost_usd: number;
  created_at: string;
}

export const adminApi = {
  createOrg: (name: string, slug: string) =>
    request("/admin/organizations", { method: "POST", body: JSON.stringify({ name, slug, plan: "starter" }) }),
  createKey: (org_id: string, name: string) =>
    request<{ key: string; prefix: string; id: string; message: string }>(
      "/admin/api-keys",
      { method: "POST", body: JSON.stringify({ org_id, name, permissions: ["read", "write"] }) }
    ),
  listKeys: (org_id: string) =>
    request<{ keys: ApiKeyItem[] }>(`/admin/api-keys/${org_id}`),
  revokeKey: (key_id: string) =>
    request(`/admin/api-keys/${key_id}`, { method: "DELETE" }),
};

// ─── Marketplace ───────────────────────────────

export interface RecommendedAgent {
  slug: string;
  name: string;
  icon: string;
  reason: string;
  role_in_flow: string;
}

export interface RecommendedTool {
  slug: string;
  name: string;
  icon: string;
  reason: string;
  used_by_agent: string;
}

export interface FlowStep {
  id: string;
  label: string;
  type: "input" | "llm" | "agent" | "tool" | "output";
  component: string;
  icon: string;
  description: string;
  connects_to: string[];
}

export interface ActionPlanStep {
  step: number;
  title: string;
  description: string;
  agents: string[];
  tools: string[];
  llm: string;
  expected_output: string;
}

export interface FlowRecommendation {
  product_summary: string;
  recommended_llm: string;
  llm_reason: string;
  recommended_agents: RecommendedAgent[];
  recommended_tools: RecommendedTool[];
  flow_steps: FlowStep[];
  action_plan: ActionPlanStep[];
  api_snippet: string;
}

export interface LLMCard {
  id: string;
  display_name: string;
  provider: string;
  description: string;
  best_for: string[];
  pricing: { input_per_1m: number; output_per_1m: number };
}

export interface RepoCard {
  name: string;
  full_name: string;
  description: string;
  stars: number;
  forks: number;
  url: string;
  language: string;
  topics: string[];
}

export const marketplaceApi = {
  agents: () => request<{ agents: AgentInfo[]; total: number; categories: string[] }>("/v1/marketplace/agents"),
  tools: () => request<{ tools: ToolInfo[]; total: number; categories: string[] }>("/v1/marketplace/tools"),
  llms: () => request<{ llms: LLMCard[]; total: number }>("/v1/marketplace/llms"),
  repos: () => request<{ repos: RepoCard[]; total: number }>("/v1/marketplace/repos"),
  recommend: (product_description: string, use_cases: string[]) =>
    request<FlowRecommendation>("/v1/marketplace/recommend", {
      method: "POST",
      body: JSON.stringify({ product_description, use_cases }),
    }),
};

export interface ApiKeyItem {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  permissions: string[];
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string | null;
}
