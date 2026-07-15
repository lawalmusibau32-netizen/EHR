"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  Calendar,
  FileText,
  UserCog,
  Shield,
  ClipboardList,
  UserPlus,
  Pill,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["administrator", "doctor", "nurse", "receptionist"] },
  { href: "/patients", label: "Patients", icon: Users, roles: ["administrator", "doctor", "nurse", "receptionist"] },
  { href: "/appointments", label: "Appointments", icon: Calendar, roles: ["administrator", "doctor", "nurse", "receptionist"] },
  { href: "/records", label: "Medical Records", icon: FileText, roles: ["administrator", "doctor", "nurse"] },
  { href: "/supplies", label: "Inventory", icon: Pill, roles: ["administrator", "doctor", "nurse", "receptionist"] },
  { href: "/users", label: "User Management", icon: UserCog, roles: ["administrator"] },
  { href: "/users/register", label: "Register User", icon: UserPlus, roles: ["administrator"] },
  { href: "/audit-logs", label: "Audit Logs", icon: ClipboardList, roles: ["administrator"] },
  { href: "/security", label: "Security", icon: Shield, roles: ["administrator"] },
];

interface SidebarProps {
  roleKey: string;
}

export function Sidebar({ roleKey }: SidebarProps) {
  const pathname = usePathname();

  const visibleItems = navItems.filter((item) => item.roles.includes(roleKey));

  return (
    <aside className="w-64 glass-sidebar flex flex-col h-full shrink-0">
      <div className="p-4 border-b border-sidebar-border/30">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-primary-foreground font-bold text-sm shadow-lg shadow-primary/20 group-hover:shadow-primary/30 transition-all duration-300">
              H
            </div>
            <div className="absolute -inset-0.5 rounded-xl bg-gradient-to-br from-primary/30 to-transparent blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
          <div>
            <div className="font-semibold text-sm text-sidebar-foreground/90">EHR</div>
            <div className="text-[10px] text-muted-foreground/60 -mt-0.5 tracking-wide">EHR Platform</div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto scrollbar-thin">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-300 relative overflow-hidden group",
                isActive
                  ? "bg-primary/10 text-primary font-medium border border-primary/20 shadow-[0_0_15px_rgba(6,182,212,0.06)]"
                  : "text-sidebar-foreground/70 hover:text-sidebar-foreground/90 hover:bg-white/[0.04] border border-transparent"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-gradient-to-b from-primary to-primary/60" />
              )}
              <Icon className={cn("h-4 w-4 shrink-0 transition-transform duration-300", isActive && "scale-110")} />
              <span className="relative z-10">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-sidebar-border/30">
        <div className="text-[10px] uppercase text-muted-foreground/50 tracking-widest font-medium">v2.0.0</div>
        <div className="text-xs text-muted-foreground/40 mt-0.5">Secure • Modular • Scalable</div>
      </div>
    </aside>
  );
}
