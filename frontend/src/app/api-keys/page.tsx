"use client";
import { useState, useEffect } from "react";
import {
  Plus, Copy, Check, Trash2, Eye, EyeOff, Shield, AlertTriangle, Key, Loader2,
} from "lucide-react";
import Header from "@/components/Header";
import { adminApi, API_BASE, getApiKey, setApiKey, type ApiKeyItem } from "@/lib/api";

const PLANS = [
  { id: "starter", label: "Starter", rpm: 60, daily: 10000, features: ["All built-in agents", "All tools", "Basic analytics"] },
  { id: "pro", label: "Pro", rpm: 300, daily: 100000, features: ["Everything in Starter", "Priority routing", "Advanced analytics", "Custom agents"] },
  { id: "enterprise", label: "Enterprise", rpm: 2000, daily: 1000000, features: ["Everything in Pro", "Custom LLMs", "SLA guarantee", "Dedicated support", "SSO"] },
];

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="p-1.5 text-slate-400 hover:text-white rounded transition-colors">
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

// Derive org_id and stored keys from localStorage
function getStoredOrgId(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("gw_org_id") || "";
}

function setStoredOrgId(id: string) {
  if (typeof window !== "undefined") localStorage.setItem("gw_org_id", id);
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyModal, setNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [revoking, setRevoking] = useState<string | null>(null);

  // Load keys on mount using stored org_id, or seed from existing stored key
  useEffect(() => {
    const orgId = getStoredOrgId();
    if (!orgId) {
      setLoading(false);
      return;
    }
    adminApi.listKeys(orgId)
      .then((d) => setKeys(d.keys || []))
      .catch(() => setKeys([]))
      .finally(() => setLoading(false));
  }, []);

  const createKey = async () => {
    if (!newKeyName.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      let orgId = getStoredOrgId();

      // If no org exists yet, create one first
      if (!orgId) {
        const slug = `user-${Date.now().toString(36)}`;
        const org = await adminApi.createOrg(newKeyName, slug) as { id: string };
        orgId = org.id;
        setStoredOrgId(orgId);
      }

      const result = await adminApi.createKey(orgId, newKeyName);
      const rawKey = result.key;

      // Save as the active key in localStorage so all API calls use it
      setApiKey(rawKey);

      const newEntry: ApiKeyItem = {
        id: result.id,
        name: newKeyName,
        prefix: result.prefix,
        is_active: true,
        permissions: ["read", "write"],
        last_used_at: null,
        expires_at: null,
        created_at: new Date().toISOString(),
      };
      setKeys((prev) => [newEntry, ...prev]);
      setCreatedKey(rawKey);
      setNewKeyName("");
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : "Failed to create key");
    } finally {
      setCreating(false);
    }
  };

  const revokeKey = async (id: string) => {
    setRevoking(id);
    try {
      await adminApi.revokeKey(id);
      setKeys((prev) => prev.map((k) => k.id === id ? { ...k, is_active: false } : k));
    } catch {
      // Optimistic update failed — revert
    } finally {
      setRevoking(null);
    }
  };

  const activeKey = getApiKey();

  return (
    <div className="animate-fade-in">
      <Header title="API Keys" subtitle="Manage access credentials for your organization" />

      <div className="p-6 space-y-6 max-w-5xl">
        {/* Integration example */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
            <Key size={16} className="text-indigo-400" />
            Quick Integration
          </h3>
          <pre className="text-xs overflow-x-auto text-slate-300">{`# Submit any task to the AI Gateway
curl -X POST ${API_BASE}/v1/query \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Research the latest trends in AI agents",
    "context_url": "https://example.com/report.pdf"
  }'

# The gateway automatically:
# ✓ Extracts context from the URL
# ✓ Selects the best LLM (Claude Opus/Sonnet/Haiku)
# ✓ Routes to the Research Agent
# ✓ Executes web_search + web_scrape tools
# ✓ Returns structured response with metadata`}</pre>
        </div>

        {/* Active key banner */}
        {activeKey && activeKey !== "gw-demo-key-change-in-production-12345678" && (
          <div className="flex items-center gap-3 bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-4">
            <Check size={15} className="text-emerald-400 shrink-0" />
            <div>
              <div className="text-emerald-400 text-sm font-medium">Active API key is set</div>
              <div className="text-xs text-emerald-300/60 font-mono mt-0.5">{activeKey.slice(0, 16)}••••••••</div>
            </div>
          </div>
        )}

        {/* Keys list */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between p-5 border-b border-slate-800">
            <h3 className="text-white font-semibold">API Keys</h3>
            <button
              onClick={() => { setNewKeyModal(true); setCreatedKey(null); setCreateError(null); }}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <Plus size={15} />
              Create Key
            </button>
          </div>

          {/* New key modal */}
          {newKeyModal && (
            <div className="p-5 border-b border-slate-800 bg-slate-800/30">
              {createdKey ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400 text-sm">
                    <Check size={16} />
                    <span>API key created! Copy it now — it won&apos;t be shown again.</span>
                  </div>
                  <div className="flex items-center gap-2 bg-slate-800 border border-emerald-500/30 rounded-lg px-4 py-3 font-mono text-sm text-emerald-300">
                    <span className="flex-1 break-all">{createdKey}</span>
                    <CopyBtn text={createdKey} />
                  </div>
                  <button onClick={() => setNewKeyModal(false)} className="text-xs text-slate-400 hover:text-slate-300">
                    Done
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <input
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      placeholder="Key name (e.g. Production, CI/CD)"
                      className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500"
                      onKeyDown={(e) => e.key === "Enter" && createKey()}
                      disabled={creating}
                    />
                    <button onClick={createKey} disabled={!newKeyName.trim() || creating}
                      className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                      {creating ? <Loader2 size={14} className="animate-spin" /> : null}
                      Create
                    </button>
                    <button onClick={() => setNewKeyModal(false)} className="text-slate-400 hover:text-slate-300 px-3 py-2 text-sm">
                      Cancel
                    </button>
                  </div>
                  {createError && (
                    <p className="text-xs text-red-400">{createError}</p>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="divide-y divide-slate-800">
            {loading ? (
              <div className="p-8 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
                <Loader2 size={14} className="animate-spin" /> Loading keys...
              </div>
            ) : keys.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No API keys yet.{" "}
                <button onClick={() => { setNewKeyModal(true); setCreatedKey(null); }} className="text-indigo-400 hover:underline">
                  Create your first key →
                </button>
              </div>
            ) : (
              keys.map((key) => (
                <div key={key.id} className="flex items-center gap-4 px-5 py-4">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${key.is_active ? "bg-emerald-400" : "bg-slate-600"}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white text-sm font-medium">{key.name}</span>
                      {!key.is_active && <span className="text-xs text-red-400 bg-red-900/20 px-1.5 py-0.5 rounded">Revoked</span>}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="text-xs text-slate-400 font-mono">
                        {key.prefix}•••
                      </code>
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      {key.permissions.map((p) => (
                        <span key={p} className="text-xs text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">{p}</span>
                      ))}
                      {key.last_used_at && (
                        <span className="text-xs text-slate-600">
                          Last used: {new Date(key.last_used_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <CopyBtn text={key.prefix} />
                    {key.is_active && (
                      <button onClick={() => revokeKey(key.id)}
                        disabled={revoking === key.id}
                        className="p-1.5 text-slate-500 hover:text-red-400 rounded transition-colors disabled:opacity-50">
                        {revoking === key.id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Plans */}
        <div>
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Shield size={16} className="text-indigo-400" />
            Plans & Limits
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {PLANS.map((plan) => (
              <div key={plan.id} className={`bg-slate-900 border rounded-xl p-5 ${
                plan.id === "pro" ? "border-indigo-500/50 bg-indigo-900/10" : "border-slate-800"
              }`}>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-white font-semibold">{plan.label}</h4>
                  {plan.id === "pro" && (
                    <span className="text-xs bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-full">Popular</span>
                  )}
                </div>
                <div className="text-slate-400 text-xs space-y-1 mb-4">
                  <div>{plan.rpm} req/min</div>
                  <div>{plan.daily.toLocaleString()} req/day</div>
                </div>
                <ul className="space-y-1.5">
                  {plan.features.map((f) => (
                    <li key={f} className="text-xs text-slate-400 flex items-center gap-1.5">
                      <Check size={11} className="text-emerald-400 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Security note */}
        <div className="flex items-start gap-3 bg-amber-900/20 border border-amber-500/30 rounded-xl p-4">
          <AlertTriangle size={16} className="text-amber-400 mt-0.5 shrink-0" />
          <div className="text-sm text-amber-300/80">
            <strong>Security note:</strong> Never expose API keys in client-side code. Always use them server-side.
            Rotate keys regularly and use the minimum required permissions.
          </div>
        </div>
      </div>
    </div>
  );
}
