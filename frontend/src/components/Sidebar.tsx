"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Terminal, Bot, Wrench, Key, BarChart3,
  Zap, ExternalLink, ChevronRight, Radio, Store,
} from "lucide-react";
import clsx from "clsx";

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
          ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
          : "text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent"
      )}
    >
      <Icon size={16} className={active ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300"} />
      <span className="flex-1">{label}</span>

      {/* Live indicator on Dashboard when active */}
      {isDashboard && active && (
        <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-900/30 border border-emerald-700/40 px-1.5 py-0.5 rounded-full">
          <Radio size={8} className="animate-pulse" />
          LIVE
        </span>
      )}

      {/* Badge for agents/tools count */}
      {badge && !active && (
        <span className="text-[10px] text-slate-600 bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded-full font-medium">
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

  return (
    <aside className="fixed left-0 top-0 h-full w-[260px] bg-slate-900 border-r border-slate-800 flex flex-col z-40">

      {/* ── Logo ───────────────────────────────────────────── */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-indigo-900/40">
            <Zap size={17} className="text-white" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900" />
          </div>
          <div>
            <h1 className="font-bold text-white text-sm leading-tight tracking-tight">AI Gateway</h1>
            <p className="text-slate-500 text-[11px] mt-0.5">Orchestrator v1.0</p>
          </div>
        </div>
      </div>

      {/* ── Status badge ───────────────────────────────────── */}
      <div className="mx-4 mt-4 px-3 py-2 bg-emerald-900/20 border border-emerald-700/30 rounded-lg flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
        <span className="text-emerald-400 text-xs font-medium">All systems operational</span>
      </div>

      {/* ── Navigation ─────────────────────────────────────── */}
      <nav className="flex-1 px-3 mt-5 space-y-5 overflow-y-auto">

        {/* MAIN section */}
        <div>
          <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest px-3 mb-1.5">
            Main
          </p>
          <div className="space-y-0.5">
            {MAIN_NAV.map(({ href, label, icon }) => (
              <NavItem
                key={href}
                href={href}
                label={label}
                icon={icon}
                active={pathname === href}
                isDashboard={href === "/"}
              />
            ))}
          </div>
        </div>

        {/* MANAGEMENT section */}
        <div>
          <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest px-3 mb-1.5">
            Management
          </p>
          <div className="space-y-0.5">
            {MANAGEMENT_NAV.map(({ href, label, icon, badge }) => (
              <NavItem
                key={href}
                href={href}
                label={label}
                icon={icon}
                badge={badge}
                active={pathname === href || pathname.startsWith(href + "/")}
              />
            ))}
          </div>
        </div>
      </nav>

      {/* ── Bottom area ────────────────────────────────────── */}
      <div className="p-4 border-t border-slate-800 space-y-2">
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2.5 text-slate-400 hover:text-white text-xs px-3 py-2.5 rounded-lg hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-all group"
        >
          <ExternalLink size={13} className="shrink-0 group-hover:text-indigo-400 transition-colors" />
          <span className="font-medium">API Docs</span>
          <span className="ml-auto text-[10px] text-slate-600 group-hover:text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            Swagger
          </span>
        </a>

        <div className="px-3 py-2 bg-slate-800/40 rounded-lg border border-slate-800">
          <div className="text-[10px] text-slate-600 uppercase tracking-wide font-medium mb-1">Demo API Key</div>
          <div className="text-xs text-slate-500 font-mono truncate">gw-demo-key-change-...</div>
        </div>
      </div>
    </aside>
  );
}
