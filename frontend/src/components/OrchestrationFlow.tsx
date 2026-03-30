"use client";
import { CheckCircle2, Circle, Loader2, Brain, Cpu, Bot, Wrench, Globe, Zap } from "lucide-react";

export type StepStatus = "pending" | "active" | "complete";

export interface PipelineStep {
  id: string;
  label: string;
  status: StepStatus;
  details?: Record<string, unknown>;
}

const STEP_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  context: Globe,
  intent: Brain,
  llm_routing: Cpu,
  agents: Bot,
  tools: Wrench,
  generation: Zap,
};

const STEP_COLORS: Record<StepStatus, string> = {
  pending: "border-slate-700 bg-slate-900/40 text-slate-500",
  active: "border-indigo-500/60 bg-indigo-900/20 text-indigo-300",
  complete: "border-emerald-500/40 bg-emerald-900/10 text-emerald-300",
};

const CONNECTOR_COLORS: Record<StepStatus, string> = {
  pending: "bg-slate-700",
  active: "bg-indigo-500",
  complete: "bg-emerald-500",
};

function AgentChip({ icon, name }: { icon: string; name: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-300">
      <span>{icon}</span>{name}
    </span>
  );
}

function ToolChip({ name, success }: { name: string; success?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${
      success === false
        ? "bg-red-900/20 border-red-700/40 text-red-400"
        : "bg-slate-800 border-slate-700 text-slate-300"
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${success === false ? "bg-red-400" : "bg-emerald-400"}`} />
      {name}
    </span>
  );
}

function StepDetails({ step }: { step: PipelineStep }) {
  const d = step.details;
  if (!d) return null;

  if (step.id === "intent") {
    const cat = d.category ? String(d.category) : null;
    const cplx = d.complexity ? String(d.complexity) : null;
    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {cat && (
          <span className="px-2 py-0.5 bg-indigo-900/30 border border-indigo-700/40 rounded-full text-xs text-indigo-300">
            {cat}
          </span>
        )}
        {cplx && (
          <span className={`px-2 py-0.5 rounded-full text-xs border ${
            cplx === "high"
              ? "bg-red-900/20 border-red-700/40 text-red-300"
              : cplx === "medium"
              ? "bg-amber-900/20 border-amber-700/40 text-amber-300"
              : "bg-emerald-900/20 border-emerald-700/40 text-emerald-300"
          }`}>
            {cplx} complexity
          </span>
        )}
      </div>
    );
  }

  if (step.id === "llm_routing") {
    const llm = d.llm ? String(d.llm) : null;
    const reason = d.reason ? String(d.reason) : null;
    return (
      <div className="mt-2">
        {llm && <div className="text-xs font-semibold text-white">{llm}</div>}
        {reason && <div className="text-xs text-slate-500 mt-0.5 leading-relaxed">{reason}</div>}
      </div>
    );
  }

  if (step.id === "agents") {
    const agents = d.agents as Array<{ slug: string; name: string; icon: string; capabilities: string[] }>;
    if (!agents?.length) return <div className="mt-1 text-xs text-slate-500">No agents needed for this task</div>;
    return (
      <div className="mt-2 flex flex-wrap gap-1.5">
        {agents.map(a => <AgentChip key={a.slug} icon={a.icon} name={a.name} />)}
      </div>
    );
  }

  if (step.id === "tools") {
    const tools = d.tools as Array<{ name: string; success: boolean }>;
    if (!tools?.length) return null;
    return (
      <div className="mt-2 flex flex-wrap gap-1.5">
        {tools.map(t => <ToolChip key={t.name} name={t.name} success={t.success} />)}
      </div>
    );
  }

  if (step.id === "generation" && step.status === "complete") {
    const inputTok = typeof d.input_tokens === "number" ? d.input_tokens : null;
    const outputTok = typeof d.output_tokens === "number" ? d.output_tokens : null;
    const cost = typeof d.cost_usd === "number" ? d.cost_usd : null;
    const latency = typeof d.latency_ms === "number" ? d.latency_ms : null;
    return (
      <div className="mt-2 flex gap-3 text-xs text-slate-500">
        {inputTok != null && <span>{inputTok.toLocaleString()} in</span>}
        {outputTok != null && <span>{outputTok.toLocaleString()} out</span>}
        {cost != null && <span className="text-emerald-500">${cost.toFixed(5)}</span>}
        {latency != null && <span>{latency}ms</span>}
      </div>
    );
  }

  return null;
}

export default function OrchestrationFlow({ steps }: { steps: PipelineStep[] }) {
  if (!steps.length) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-2.5 border-b border-slate-800 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
        <span className="text-xs font-medium text-slate-400">Orchestration Pipeline</span>
      </div>

      <div className="p-4">
        {steps.map((step, i) => {
          const Icon = STEP_ICONS[step.id] || Zap;
          const isLast = i === steps.length - 1;

          return (
            <div key={step.id} className="flex gap-3">
              {/* Left: icon + connector */}
              <div className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 transition-all duration-300 ${STEP_COLORS[step.status]}`}>
                  {step.status === "active" ? (
                    <Loader2 size={14} className="animate-spin text-indigo-400" />
                  ) : step.status === "complete" ? (
                    <CheckCircle2 size={14} className="text-emerald-400" />
                  ) : (
                    <Icon size={14} />
                  )}
                </div>
                {!isLast && (
                  <div className={`w-0.5 flex-1 my-1 min-h-[16px] rounded-full transition-all duration-500 ${CONNECTOR_COLORS[step.status]}`} />
                )}
              </div>

              {/* Right: content */}
              <div className={`pb-${isLast ? "0" : "4"} min-w-0 flex-1 pt-1`}>
                <div className="text-sm font-medium text-white leading-none">{step.label}</div>
                <StepDetails step={step} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
