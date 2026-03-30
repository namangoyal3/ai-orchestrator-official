"use client";
import { useState } from "react";
import {
  Plus, Copy, Check, Trash2, Eye, EyeOff, Shield, AlertTriangle, Key,
} from "lucide-react";
import Header from "@/components/Header";

interface ApiKeyEntry {
  id: string;
  name: string;
  key?: string;
  prefix: string;
  is_active: boolean;
  permissions: string[];
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

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

const DEMO_KEYS: ApiKeyEntry[] = [
  {
    id: "1", name: "Demo Key", prefix: "gw-demo-key-...",
    is_active: true, permissions: ["read", "write", "admin"],
    last_used_at: new Date().toISOString(),
    expires_at: null,
    created_at: new Date().toISOString(),
  },
];

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyEntry[]>(DEMO_KEYS);
  const [newKeyModal, setNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [revoking, setRevoking] = useState<string | null>(null);

  const createKey = () => {
    if (!newKeyName.trim()) return;
    const rawKey = `gw-${Math.random().toString(36).slice(2)}${Math.random().toString(36).slice(2)}`;
    const newKey: ApiKeyEntry = {
      id: Math.random().toString(36).slice(2),
      name: newKeyName,
      key: rawKey,
      prefix: rawKey.slice(0, 12) + "...",
      is_active: true,
      permissions: ["read", "write"],
      last_used_at: null,
      expires_at: null,
      created_at: new Date().toISOString(),
    };
    setKeys((prev) => [newKey, ...prev]);
    setCreatedKey(rawKey);
    setNewKeyName("");
  };

  const revokeKey = (id: string) => {
    setRevoking(id);
    setTimeout(() => {
      setKeys((prev) => prev.map((k) => k.id === id ? { ...k, is_active: false } : k));
      setRevoking(null);
    }, 500);
  };

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
          <pre className="text-xs overflow-x-auto">{`# Submit any task to the AI Gateway
curl -X POST http://localhost:8000/v1/query \\
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

        {/* Keys list */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between p-5 border-b border-slate-800">
            <h3 className="text-white font-semibold">API Keys</h3>
            <button
              onClick={() => { setNewKeyModal(true); setCreatedKey(null); }}
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
                    <span>API key created! Copy it now — it won't be shown again.</span>
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
                <div className="flex items-center gap-3">
                  <input
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="Key name (e.g. Production, CI/CD)"
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500"
                    onKeyDown={(e) => e.key === "Enter" && createKey()}
                  />
                  <button onClick={createKey} disabled={!newKeyName.trim()}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                    Create
                  </button>
                  <button onClick={() => setNewKeyModal(false)} className="text-slate-400 hover:text-slate-300 px-3 py-2 text-sm">
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="divide-y divide-slate-800">
            {keys.map((key) => (
              <div key={key.id} className="flex items-center gap-4 px-5 py-4">
                <div className={`w-2 h-2 rounded-full shrink-0 ${key.is_active ? "bg-emerald-400" : "bg-slate-600"}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-white text-sm font-medium">{key.name}</span>
                    {!key.is_active && <span className="text-xs text-red-400 bg-red-900/20 px-1.5 py-0.5 rounded">Revoked</span>}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="text-xs text-slate-400 font-mono">
                      {showKey[key.id] && key.key ? key.key : key.prefix + "•••"}
                    </code>
                    {key.key && (
                      <button onClick={() => setShowKey((p) => ({ ...p, [key.id]: !p[key.id] }))}
                        className="text-slate-600 hover:text-slate-400">
                        {showKey[key.id] ? <EyeOff size={12} /> : <Eye size={12} />}
                      </button>
                    )}
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
                  <CopyBtn text={key.key || key.prefix} />
                  {key.is_active && (
                    <button onClick={() => revokeKey(key.id)}
                      disabled={revoking === key.id}
                      className="p-1.5 text-slate-500 hover:text-red-400 rounded transition-colors">
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>
              </div>
            ))}
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
