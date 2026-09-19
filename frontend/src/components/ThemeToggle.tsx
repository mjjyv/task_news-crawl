"use client";

import React, { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "./ThemeProvider";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-9 h-9 rounded-full bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
    );
  }

  return (
    <button
      onClick={toggleTheme}
      type="button"
      className="flex items-center justify-center w-9 h-9 rounded-full text-neutral-600 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
      aria-label="Chuyển chế độ sáng tối"
      title={theme === "light" ? "Bật chế độ tối" : "Bật chế độ sáng"}
    >
      {theme === "light" ? (
        <Moon className="w-5 h-5 transition-transform hover:-rotate-12 text-neutral-700" />
      ) : (
        <Sun className="w-5 h-5 transition-transform hover:rotate-45 text-amber-400" />
      )}
    </button>
  );
}
