"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard, Terminal, Bot, Wrench, Key,
  BarChart2, Zap, ExternalLink, Radio, Store, Layers, LayoutTemplate,
} from "lucide-react";
import clsx from "clsx";
import { API_BASE, getApiKey } from "@/lib/api";

const MAIN_NAV = [
  { href: "/",            label: "Dashboard",   icon: LayoutDashboard },
  { href: "/playground",  label: "Playground",  icon: Terminal },
  { href: "/marketplace", label: "Marketplace", icon: Store },
  { href: "/stacks",      label: "Stacks",      icon: Layers,          badge: "NEW" },
  { href: "/templates",   label: "Templates",   icon: LayoutTemplate,  badge: "NEW" },
];

const MANAGEMENT_NAV: { href: string; label: string; icon: React.ComponentType<{ size?: number; className?: string }>; badge?: string }[] = [
  { href: "/agents",    label: "Agents",    icon: Bot },
  { href: "/tools",     label: "Tools",     icon: Wrench },
  { href: "/api-keys",  label: "API Keys",  icon: Key },
  { href: "/analytics", label: "Analytics", icon: BarChart2 },
];

interface NavItemProps {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  badge?: string;
  active: boolean;
  isDashboard?: boolean;
}

function NavItem({ href, label, icon: Icon, badge, active, isDashboard }: NavItemProps) {
  return (
    <Link
      href={href}
      className={clsx(
        "flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[13px] font-medium transition-all group",
        active
          ? "bg-white/[0.07] text-white"
          : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
      )}
    >
      <Icon
        size={15}
        className={clsx(
          "shrink-0 transition-colors",
          active ? "text-brand-400" : "text-zinc-500 group-hover:text-zinc-300"
        )}
      />
      <span className="flex-1 leading-none">{label}</span>

      {isDashboard && active && (
        <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-1.5 py-0.5 rounded-full">
          <Radio size={7} className="animate-pulse" />
          LIVE
        </span>
      )}

      {badge && (
        <span className={clsx(
          "text-[10px] px-1.5 py-0.5 rounded-full font-semibold",
          badge === "NEW"
            ? "text-brand-300 bg-brand-500/15 border border-brand-400/20"
            : "text-zinc-500 bg-white/[0.05] border border-white/[0.08]"
        )}>
          {badge}
        </span>
      )}
    </Link>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const [activeKey, setActiveKey] = useState("");

  useEffect(() => {
    setActiveKey(getApiKey());
    const handleStorage = () => setActiveKey(getApiKey());
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const keyDisplay = activeKey
    ? activeKey.slice(0, 14) + "••••"
    : "No key set — click to add";

  return (
    <aside className="fixed left-0 top-0 h-full w-[240px] bg-[#111113] border-r border-white/[0.07] flex flex-col z-40">

      {/* Logo */}
      <div className="px-4 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-900/50">
            <Zap size={15} className="text-white" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-400 rounded-full border-[1.5px] border-[#111113] animate-pulse-glow" />
          </div>
          <div>
            <h1 className="font-semibold text-white text-[13px] leading-tight tracking-tight">AI Gateway</h1>
            <p className="text-zinc-500 text-[11px] mt-0.5 font-mono">v1.1.0</p>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="mx-3 mt-3 px-2.5 py-1.5 bg-emerald-500/[0.08] border border-emerald-500/[0.15] rounded-md flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
        <span className="text-emerald-400 text-[11px] font-medium">All systems operational</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 mt-4 space-y-4 overflow-y-auto pb-4">
        <div>
          <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest px-2.5 mb-1">
            Main
          </p>
          <div className="space-y-0.5">
            {MAIN_NAV.map(({ href, label, icon, badge }) => (
              <NavItem key={href} href={href} label={label} icon={icon} badge={badge}
                active={pathname === href} isDashboard={href === "/"} />
            ))}
          </div>
        </div>

        <div>
          <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest px-2.5 mb-1">
            Management
          </p>
          <div className="space-y-0.5">
            {MANAGEMENT_NAV.map(({ href, label, icon, badge }) => (
              <NavItem key={href} href={href} label={label} icon={icon} badge={badge}
                active={pathname === href || pathname.startsWith(href + "/")} />
            ))}
          </div>
        </div>
      </nav>

      {/* Bottom */}
      <div className="p-3 border-t border-white/[0.06] space-y-1.5">
        <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-2 text-zinc-500 hover:text-zinc-200 text-[12px] px-2.5 py-2 rounded-md hover:bg-white/[0.04] transition-colors group">
          <ExternalLink size={13} className="shrink-0" />
          <span className="font-medium">API Docs</span>
          <span className="ml-auto text-[10px] text-zinc-600 bg-white/[0.04] px-1.5 py-0.5 rounded border border-white/[0.06]">
            Swagger
          </span>
        </a>

        <Link href="/api-keys"
          className="px-2.5 py-2 bg-white/[0.03] rounded-md border border-white/[0.07] hover:border-white/[0.12] transition-colors block group">
          <div className="text-[10px] text-zinc-600 uppercase tracking-wide font-medium mb-1">Active API Key</div>
          <div className={clsx(
            "text-[11px] font-mono truncate",
            activeKey ? "text-zinc-300" : "text-zinc-600 italic"
          )}>{keyDisplay}</div>
        </Link>
      </div>
    </aside>
  );
}
