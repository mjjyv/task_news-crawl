"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ChevronDown, Grid } from "lucide-react";
import { CategoryTreeItem } from "@/lib/types";

interface MegaMenuProps {
  categories: CategoryTreeItem[];
}

export function MegaMenu({ categories }: MegaMenuProps) {
  const [activeMenu, setActiveMenu] = useState<number | string | null>(null);

  // Define priority slugs to show in primary navbar
  const primarySlugs = [
    "thoi-su",
    "khoa-hoc-cong-nghe",
    "kinh-doanh",
    "giai-tri",
    "the-gioi",
    "the-thao",
  ];

  // Separate primary categories from other categories
  const primaryCats: CategoryTreeItem[] = [];
  const otherCats: CategoryTreeItem[] = [];

  // Match primary categories in preferred order
  primarySlugs.forEach((slug) => {
    const found = categories.find((c) => c.slug === slug);
    if (found) primaryCats.push(found);
  });

  // Remaining categories
  categories.forEach((cat) => {
    if (!primaryCats.some((p) => p.id === cat.id)) {
      otherCats.push(cat);
    }
  });

  // If primaryCats is empty (e.g. initial load or different slugs), slice first 6
  const finalPrimary = primaryCats.length > 0 ? primaryCats : categories.slice(0, 6);
  const finalOthers = primaryCats.length > 0 ? otherCats : categories.slice(6);

  return (
    <nav className="hidden lg:flex items-center space-x-1 font-mono text-xs">
      <Link
        href="/"
        className="px-2.5 py-1 text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] border border-transparent transition-colors uppercase tracking-wider whitespace-nowrap shrink-0"
      >
        [ TRANG CHỦ ]
      </Link>

      {finalPrimary.map((cat) => {
        const hasChildren = cat.children && cat.children.length > 0;
        const isOpen = activeMenu === cat.id;

        return (
          <div
            key={cat.id}
            className="relative"
            onMouseEnter={() => setActiveMenu(cat.id)}
            onMouseLeave={() => setActiveMenu(null)}
          >
            <Link
              href={`/category/${cat.slug}`}
              className={`px-2.5 py-1 text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] border transition-colors flex items-center gap-1 uppercase tracking-wider whitespace-nowrap shrink-0 ${
                isOpen ? "border-[#E61919] text-[#EAEAEA] bg-[#121212]" : "border-transparent"
              }`}
            >
              <span>{cat.name}</span>
              {hasChildren && (
                <ChevronDown
                  className={`w-3 h-3 text-[#666] transition-transform duration-200 ${
                    isOpen ? "rotate-180 text-[#E61919]" : ""
                  }`}
                />
              )}
            </Link>

            {/* Dropdown Menu for Subcategories */}
            {hasChildren && isOpen && (
              <div className="absolute top-full left-0 mt-1 w-60 p-2 bg-[#121212] border border-[#262626] shadow-2xl z-50 animate-in fade-in duration-150">
                <div className="p-2 border-b border-[#262626] mb-1">
                  <Link
                    href={`/category/${cat.slug}`}
                    className="text-[10px] font-bold uppercase tracking-wider text-[#E61919] hover:underline block whitespace-nowrap"
                  >
                    [ TẤT CẢ // {cat.name} ({cat.article_count} BÀI) ]
                  </Link>
                </div>
                <div className="space-y-0.5 max-h-80 overflow-y-auto">
                  {cat.children.map((sub) => (
                    <Link
                      key={sub.id}
                      href={`/category/${sub.slug}`}
                      className="flex items-center justify-between px-2.5 py-1.5 text-xs text-[#8A8A8A] hover:bg-[#1A1A1A] hover:text-[#EAEAEA] transition-colors whitespace-nowrap"
                    >
                      <span>// {sub.name}</span>
                      {sub.article_count > 0 && (
                        <span className="text-[10px] px-1 py-0.2 bg-[#0A0A0A] border border-[#262626] text-[#666] ml-2">
                          {sub.article_count}
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* "MORE CATEGORIES" Mega Dropdown */}
      {finalOthers.length > 0 && (
        <div
          className="relative"
          onMouseEnter={() => setActiveMenu("more")}
          onMouseLeave={() => setActiveMenu(null)}
        >
          <button
            type="button"
            className={`px-2.5 py-1 text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] border transition-colors flex items-center gap-1 uppercase tracking-wider whitespace-nowrap shrink-0 ${
              activeMenu === "more" ? "border-[#E61919] text-[#EAEAEA] bg-[#121212]" : "border-transparent"
            }`}
          >
            <Grid className="w-3 h-3 text-[#E61919]" />
            <span>[ + TẤT CẢ ({categories.length}) ]</span>
            <ChevronDown
              className={`w-3 h-3 text-[#666] transition-transform duration-200 ${
                activeMenu === "more" ? "rotate-180 text-[#E61919]" : ""
              }`}
            />
          </button>

          {activeMenu === "more" && (
            <div className="absolute top-full right-0 mt-1 w-[560px] p-4 bg-[#121212] border border-[#262626] shadow-2xl z-50 animate-in fade-in duration-150">
              <div className="flex items-center justify-between pb-2 border-b border-[#262626] mb-3">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#E61919]">
                  INDEX // TOÀN BỘ CHUYÊN MỤC BÁO CHÍ ({categories.length} SECTORS)
                </span>
                <span className="text-[9px] text-[#666]">
                  CHỌN ĐỂ TRUY CẬP
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 max-h-[380px] overflow-y-auto pr-1">
                {categories.map((cat) => (
                  <Link
                    key={cat.id}
                    href={`/category/${cat.slug}`}
                    className="flex items-center justify-between p-2 bg-[#171717] border border-[#262626] hover:border-[#E61919] hover:bg-[#1C1C1C] text-[#8A8A8A] hover:text-[#EAEAEA] transition-colors"
                  >
                    <span className="text-xs truncate font-mono">// {cat.name}</span>
                    <span className="text-[9px] px-1 py-0.5 bg-[#0A0A0A] border border-[#262626] text-[#666] ml-1 shrink-0">
                      {cat.article_count}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}

