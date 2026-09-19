"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Command } from "lucide-react";
import { CategoryTreeItem } from "@/lib/types";
import { MegaMenu } from "./MegaMenu";
import { MobileNav } from "./MobileNav";
import { ThemeToggle } from "./ThemeToggle";
import { CrawlerHealthBadge } from "./CrawlerHealthBadge";
import { SearchModal } from "./SearchModal";

interface HeaderProps {
  categories?: CategoryTreeItem[];
}

export function Header({ categories = [] }: HeaderProps) {
  const [searchOpen, setSearchOpen] = useState(false);

  // Global hotkey: Ctrl+K or Cmd+K or '/' to open search modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      } else if (
        e.key === "/" &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        e.preventDefault();
        setSearchOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-40 w-full bg-white/95 dark:bg-neutral-900/95 backdrop-blur border-b border-neutral-200 dark:border-neutral-800 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-4">
            {/* Left: Mobile Nav + Logo */}
            <div className="flex items-center gap-3">
              <MobileNav categories={categories} onOpenSearch={() => setSearchOpen(true)} />

              <Link href="/" className="flex items-center gap-2.5 group">
                <span className="w-8 h-8 rounded-xl bg-brand-600 text-white font-black flex items-center justify-center text-base shadow group-hover:bg-brand-700 transition-colors">
                  V
                </span>
                <div className="flex flex-col">
                  <span className="font-extrabold text-base sm:text-lg tracking-tight text-neutral-900 dark:text-white leading-none">
                    VnExpress<span className="text-brand-600 dark:text-brand-400">Reader</span>
                  </span>
                  <span className="text-[10px] text-neutral-400 font-medium tracking-wide">
                    Tối giản • Không quảng cáo
                  </span>
                </div>
              </Link>
            </div>

            {/* Middle: Desktop MegaMenu */}
            <div className="hidden lg:flex flex-1 justify-center px-4">
              <MegaMenu categories={categories} />
            </div>

            {/* Right: Search trigger + Crawler status + Theme toggle */}
            <div className="flex items-center gap-2.5">
              {/* Quick Search Button */}
              <button
                onClick={() => setSearchOpen(true)}
                type="button"
                className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-xs font-medium transition-colors border border-neutral-200/50 dark:border-neutral-700/50"
                title="Tìm kiếm nhanh (Ctrl + K)"
              >
                <Search className="w-3.5 h-3.5 text-neutral-400" />
                <span className="hidden md:inline">Tìm kiếm...</span>
                <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700 text-neutral-400">
                  <Command className="w-2.5 h-2.5" />K
                </kbd>
              </button>

              {/* Mobile Search Icon button */}
              <button
                onClick={() => setSearchOpen(true)}
                type="button"
                className="sm:hidden p-2 text-neutral-600 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg"
                aria-label="Tìm kiếm"
              >
                <Search className="w-5 h-5" />
              </button>

              {/* Crawler Health Pulse */}
              <CrawlerHealthBadge />

              {/* Dark/Light mode toggle */}
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Global Search Modal */}
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
