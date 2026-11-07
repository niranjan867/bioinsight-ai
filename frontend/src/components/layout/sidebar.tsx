"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Dna,
  Activity,
  FlaskConical,
  Layers,
  HeartPulse,
  Atom,
  FolderKanban,
  FileText,
  Server,
  Bot,
  Crosshair,
} from "lucide-react";
import { cn } from "cn";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const mainNavItems: NavItem[] = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Research Projects", href: "/projects", icon: FolderKanban },
];

const intelligenceNavItems: NavItem[] = [
  { name: "Gene Intelligence", href: "/genes", icon: Dna },
  { name: "Protein Intelligence", href: "/proteins", icon: Activity },
  { name: "Sequence Laboratory", href: "/sequences", icon: FlaskConical },
  { name: "Structure Explorer", href: "/structures", icon: Layers },
  { name: "Protein-Ligand Docking", href: "/interactions", icon: Crosshair },
  { name: "Disease Intelligence", href: "/diseases", icon: HeartPulse },
  { name: "Compound Intelligence", href: "/compounds", icon: Atom },
];

const workspaceNavItems: NavItem[] = [
  { name: "AI Research Assistant", href: "/assistant", icon: Bot, badge: "AI" },
  { name: "Research Reports", href: "/reports", icon: FileText },
  { name: "System Diagnostics", href: "/api-test", icon: Server, badge: "Live" },
];

interface SidebarProps {
  onNavigate?: () => void;
  className?: string;
}

export function Sidebar({ onNavigate, className }: SidebarProps) {
  const pathname = usePathname();

  const renderNavGroup = (title: string, items: NavItem[]) => (
    <div className="py-2">
      <h3 className="px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/80">
        {title}
      </h3>
      <div className="mt-2 space-y-1">
        {items.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "group flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground shadow-xs font-semibold"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-transform group-hover:scale-105",
                    isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground"
                  )}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.2 text-[10px] font-medium leading-normal",
                    isActive
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-primary/10 text-primary"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );

  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col border-r border-border bg-card/60 backdrop-blur-xs",
        className
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center border-b border-border px-5">
        <Link
          href="/"
          onClick={onNavigate}
          className="flex items-center gap-2.5 transition-opacity hover:opacity-90"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs">
            <Dna className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold tracking-tight text-foreground">
                BioInsight AI
              </span>
              <span className="rounded bg-primary/10 px-1 py-0.2 text-[9px] font-bold tracking-wider text-primary uppercase">
                Platform
              </span>
            </div>
            <p className="text-[10px] font-medium text-muted-foreground">
              Bioinformatics Research
            </p>
          </div>
        </Link>
      </div>

      {/* Nav Scroll Area */}
      <div className="flex-1 overflow-y-auto px-3 py-3 scrollbar-thin">
        {renderNavGroup("Navigation", mainNavItems)}
        <div className="my-2 border-t border-border/50" />
        {renderNavGroup("Intelligence Modules", intelligenceNavItems)}
        <div className="my-2 border-t border-border/50" />
        {renderNavGroup("Management", workspaceNavItems)}
      </div>

      {/* Footer Workspace Info */}
      <div className="border-t border-border p-3.5">
        <div className="rounded-lg border border-border/80 bg-muted/40 p-2.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="font-semibold text-foreground">Active Workspace</span>
            <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Connected
            </span>
          </div>
          <p className="mt-1 truncate text-[11px] text-muted-foreground">
            Computational Biology Lab
          </p>
          <div className="mt-2 flex items-center justify-between text-[10px] text-muted-foreground/80 border-t border-border/50 pt-1.5">
            <span>FastAPI + PostgreSQL</span>
            <span className="font-mono">v0.1.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

