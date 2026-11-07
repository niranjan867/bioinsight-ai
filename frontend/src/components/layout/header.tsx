"use client";

import Link from "next/link";
import {
  Search,
  FlaskConical,
  Menu,
  Bot,
  LogIn,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuth();

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

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
          <span className="text-muted-foreground">Multi-Omics & Systems Biology</span>
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

      {/* Right: AI Assistant, Diagnostics Pill, Profile */}
      <div className="flex items-center gap-2 md:gap-3">
        {/* AI Research Assistant Pill */}
        <Link href="/assistant">
          <Button
            size="sm"
            variant="outline"
            className="h-8 gap-1.5 border-primary/30 bg-primary/5 text-primary hover:bg-primary/10 text-xs font-semibold"
          >
            <Bot className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">AI Assistant</span>
          </Button>
        </Link>

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

        {/* User Profile or Login Action */}
        <div className="flex items-center gap-2 pl-2 border-l border-border/60">
          {user ? (
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xs border border-primary/20">
                {getInitials(user.full_name)}
              </div>
              <div className="hidden lg:block text-left">
                <div className="text-xs font-semibold leading-tight text-foreground">
                  {user.full_name}
                </div>
                <div className="text-[10px] text-muted-foreground truncate max-w-[140px]">
                  {user.institution || user.email}
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                title="Sign Out"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
              >
                <LogOut className="h-3.5 w-3.5" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <Link href="/login">
                <Button size="sm" variant="ghost" className="h-8 text-xs gap-1.5">
                  <LogIn className="h-3.5 w-3.5" />
                  <span>Sign In</span>
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="h-8 text-xs font-medium">
                  Register
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
