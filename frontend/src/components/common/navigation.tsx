"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Cloud, MonitorDown, LibraryBig, Download } from "lucide-react";
import { cn } from "@/lib/utils";
import { PATHS } from "@/lib/paths";

export default function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: PATHS.HOME, label: "Local", icon: Home },
    { href: PATHS.RECORD, label: "Gravar", icon: MonitorDown },
    { href: PATHS.LIBRARY, label: "Biblioteca", icon: LibraryBig },
    { href: PATHS.DRIVE, label: "Drive", icon: Cloud },
  ];

  return (
    <nav className="flex items-center gap-2 md:gap-3">
      {/* Navigation Links */}
      <div className="hidden md:flex items-center gap-1">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-all duration-300",
                isActive
                  ? "bg-white/10 text-teal border border-teal/30 shadow-glow-teal"
                  : "text-muted-foreground hover:text-white hover:bg-white/5 border border-transparent"
              )}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center transition-all",
                  isActive
                    ? "bg-teal/20 text-teal"
                    : "bg-white/5 text-muted-foreground group-hover:text-white"
                )}
              >
                <Icon className="h-4 w-4" />
              </div>
              <span className="text-sm">{link.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Mobile Navigation */}
      <div className="flex md:hidden items-center gap-1">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "p-2 rounded-full transition-all duration-300",
                isActive
                  ? "bg-teal/20 text-teal border border-teal/30"
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              )}
              title={link.label}
            >
              <Icon className="h-5 w-5" />
            </Link>
          );
        })}
      </div>

      {/* CTA Button */}
      <Link
        href={PATHS.HOME}
        className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full btn-gradient-yellow"
      >
        <Download className="h-4 w-4" />
        <span className="text-sm font-semibold">Baixar</span>
      </Link>
    </nav>
  );
}
