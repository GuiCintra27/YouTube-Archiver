"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/common/theme-provider";
import { Button } from "@/components/ui/button";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <Button
      variant="outline"
      size="icon"
      aria-label={isDark ? "Usar tema claro" : "Usar tema escuro"}
      onClick={toggleTheme}
      className="relative"
    >
      <Sun className="h-4 w-4 transition-transform duration-200 scale-100 rotate-0 dark:-rotate-90 dark:scale-0" />
      <Moon className="h-4 w-4 absolute transition-transform duration-200 scale-0 rotate-90 dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Alternar tema</span>
    </Button>
  );
}
