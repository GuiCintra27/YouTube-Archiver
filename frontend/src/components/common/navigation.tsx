"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Cloud, MonitorDown, LibraryBig } from "lucide-react";
import { cn } from "@/lib/utils";
import { PATHS } from "@/lib/paths";

export default function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: PATHS.HOME, label: "Local", icon: Home },
    { href: PATHS.RECORD, label: "Gravar", icon: MonitorDown },
    { href: PATHS.LIBRARY, label: "Biblioteca", icon: LibraryBig },
    { href: PATHS.DRIVE, label: "Google Drive", icon: Cloud },
  ];

  return (
    <nav className="flex gap-2">
      {links.map((link) => {
        const Icon = link.icon;
        const isActive = pathname === link.href;

        return (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
              isActive
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-muted"
            )}
          >
            <Icon className="h-4 w-4" />
            <span className="hidden sm:inline">{link.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
