"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LayoutDashboard, Terminal, Bot, Wrench, Key, ChartBar as BarChart3, Zap, ExternalLink, ChevronRight, Radio, Store } from "lucide-react";
import clsx from "clsx";
import { API_BASE, getApiKey } from "@/lib/api";

const MAIN_NAV = [
  { href: "/",            label: "Dashboard",   icon: LayoutDashboard },
  { href: "/playground",  label: "Playground",  icon: Terminal },
  { href: "/marketplace", label: "Marketplace", icon: Store, badge: "NEW" },
];

const MANAGEMENT_NAV = [
  { href: "/agents",    label: "Agents",    icon: Bot,      badge: "7" },
  { href: "/tools",     label: "Tools",     icon: Wrench,   badge: "15" },
  { href: "/api-keys",  label: "API Keys",  icon: Key },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
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
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group",
        active
          ? "bg-indigo-50 text-indigo-700 border border-indigo-200"
          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent"
      )}
    >
      <Icon size={16} className={active ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-600"} />
      <span className="flex-1">{label}</span>

      {isDashboard && active && (
        <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-600 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full">
          <Radio size={8} className="animate-pulse" />
          LIVE
        </span>
      )}

      {badge && !active && (
        <span className="text-[10px] text-slate-400 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded-full font-medium">
          {badge}
        </span>
      )}

      {active && !isDashboard && (
        <ChevronRight size={13} className="text-indigo-500 shrink-0" />
      )}
    </Link>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const [activeKey, setActiveKey] = useState("");

  useEffect(() => {
    setActiveKey(getApiKey());
  }, []);

  const keyDisplay = activeKey
    ? activeKey.slice(0, 14) + "••••"
    : "No key set — click to add";

  return (
    <aside className="fixed left-0 top-0 h-full w-[260px] bg-white border-r border-slate-200 flex flex-col z-40">

      {/* Logo */}
      <div className="p-5 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-indigo-700 flex items-center justify-center shadow-md shadow-indigo-200">
            <Zap size={17} className="text-white" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white" />
          </div>
          <div>
            <h1 className="font-bold text-slate-900 text-sm leading-tight tracking-tight">AI Gateway</h1>
            <p className="text-slate-400 text-[11px] mt-0.5">Orchestrator v1.0</p>
          </div>
        </div>
      </div>

      {/* Status badge */}
      <div className="mx-4 mt-4 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
        <span className="text-emerald-700 text-xs font-medium">All systems operational</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 mt-5 space-y-5 overflow-y-auto">
        <div>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest px-3 mb-1.5">
            Main
          </p>
          <div className="space-y-0.5">
            {MAIN_NAV.map(({ href, label, icon }) => (
              <NavItem key={href} href={href} label={label} icon={icon}
                active={pathname === href} isDashboard={href === "/"} />
            ))}
          </div>
        </div>

        <div>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest px-3 mb-1.5">
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

      {/* Bottom area */}
      <div className="p-4 border-t border-slate-100 space-y-2">
        <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-2.5 text-slate-500 hover:text-slate-900 text-xs px-3 py-2.5 rounded-lg hover:bg-slate-100 border border-transparent hover:border-slate-200 transition-all group">
          <ExternalLink size={13} className="shrink-0 group-hover:text-indigo-500 transition-colors" />
          <span className="font-medium">API Docs</span>
          <span className="ml-auto text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
            Swagger
          </span>
        </a>

        <Link href="/api-keys"
          className="px-3 py-2 bg-slate-50 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors block">
          <div className="text-[10px] text-slate-400 uppercase tracking-wide font-medium mb-1">Active API Key</div>
          <div className="text-xs text-slate-500 font-mono truncate">{keyDisplay}</div>
        </Link>
      </div>
    </aside>
  );
}
