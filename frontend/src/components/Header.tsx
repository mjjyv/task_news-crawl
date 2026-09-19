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
      <header className="sticky top-0 z-40 w-full bg-[#0A0A0A]/95 backdrop-blur border-b border-[#262626] text-[#EAEAEA] transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-4">
            {/* Left: Mobile Nav + Logo */}
            <div className="flex items-center gap-3">
              <MobileNav categories={categories} onOpenSearch={() => setSearchOpen(true)} />

              <Link href="/" className="flex items-center gap-2.5 group">
                <span className="px-2.5 py-1 bg-[#E61919] text-white font-mono font-black text-xs tracking-widest border border-[#E61919] shadow-[0_0_10px_rgba(230,25,25,0.4)]">
                  VNE
                </span>
                <div className="flex flex-col">
                  <span className="font-mono font-black text-sm sm:text-base tracking-wider text-[#EAEAEA] leading-none uppercase">
                    VnExpress<span className="text-[#E61919]"> // TELEMETRY</span>
                  </span>
                  <span className="font-mono text-[9px] text-[#8A8A8A] tracking-widest uppercase mt-0.5">
                    TACTICAL WIRE • DECLASSIFIED
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
                className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-[#141414] text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] text-xs font-mono tracking-wider transition-colors border border-[#262626]"
                title="Tìm kiếm nhanh (Ctrl + K)"
              >
                <Search className="w-3.5 h-3.5 text-[#8A8A8A]" />
                <span className="hidden md:inline">[ SEARCH // CTRL+K ]</span>
                <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1 py-0.5 text-[9px] font-mono bg-[#0A0A0A] border border-[#333] text-[#8A8A8A]">
                  <Command className="w-2.5 h-2.5" />K
                </kbd>
              </button>

              {/* Mobile Search Icon button */}
              <button
                onClick={() => setSearchOpen(true)}
                type="button"
                className="sm:hidden p-2 text-[#8A8A8A] hover:text-[#EAEAEA] hover:bg-[#141414] border border-[#262626]"
                aria-label="Tìm kiếm"
              >
                <Search className="w-4 h-4" />
              </button>

              {/* Crawler Health Pulse */}
              <CrawlerHealthBadge />
            </div>
          </div>
        </div>
      </header>

      {/* Global Search Modal */}
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
