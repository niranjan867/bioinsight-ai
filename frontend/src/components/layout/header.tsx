"use client";

import Link from "next/link";
import {
  Search,
  Bell,
  FlaskConical,
  Menu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-background/95 px-4 md:px-6 backdrop-blur-sm">
      {/* Left: Mobile Toggle & Workspace Indicator */}
      <div className="flex items-center gap-3 md:gap-4">
        {onMenuToggle && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuToggle}
            className="md:hidden"
            aria-label="Toggle navigation menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}

        <div className="hidden items-center gap-2 rounded-lg border border-border/80 bg-muted/30 px-3 py-1.5 text-xs sm:flex">
          <FlaskConical className="h-3.5 w-3.5 text-primary" />
          <span className="font-medium text-foreground">Workspace:</span>
          <span className="text-muted-foreground">Human Genetics & Multi-Omics</span>
        </div>
      </div>

      {/* Center: Global Search Bar */}
      <div className="flex flex-1 max-w-md mx-4">
        <div className="relative w-full">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search genes, proteins, diseases, compounds..."
            className="w-full pl-9 pr-12 text-xs bg-muted/30 border-border focus-visible:bg-background h-9"
          />
          <kbd className="absolute right-2 top-2 hidden select-none rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground sm:inline-block">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right: Diagnostics Pill, Notifications, Profile */}
      <div className="flex items-center gap-2 md:gap-3">
        {/* System Health Quick Pill */}
        <Link href="/api-test" className="hidden sm:inline-block">
          <Badge
            variant="outline"
            className="gap-1.5 py-1 px-2.5 text-[11px] font-medium border-border/80 hover:bg-muted/80 transition-colors"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-foreground">System Health</span>
          </Badge>
        </Link>

        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9 text-muted-foreground hover:text-foreground"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-primary" />
        </Button>

        {/* User Profile Avatar */}
        <div className="flex items-center gap-2.5 pl-1 border-l border-border/60">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xs border border-primary/20">
            DR
          </div>
          <div className="hidden lg:block text-left">
            <div className="text-xs font-semibold leading-tight text-foreground">
              Dr. Researcher
            </div>
            <div className="text-[10px] text-muted-foreground">
              Computational Biology Lab
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

