"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ChevronDown } from "lucide-react";
import { CategoryTreeItem } from "@/lib/types";

interface MegaMenuProps {
  categories: CategoryTreeItem[];
}

export function MegaMenu({ categories }: MegaMenuProps) {
  const [activeMenu, setActiveMenu] = useState<number | null>(null);

  return (
    <nav className="flex items-center gap-1 font-mono text-xs overflow-x-auto md:overflow-visible md:flex-wrap py-1.5 scrollbar-none">
      <Link
        href="/"
        className="px-2.5 py-1 text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] border border-transparent transition-colors uppercase tracking-wider shrink-0 whitespace-nowrap"
      >
        [ TRANG CHỦ ]
      </Link>

      {categories.map((cat) => {
        const hasChildren = cat.children && cat.children.length > 0;
        const isOpen = activeMenu === cat.id;

        return (
          <div
            key={cat.id}
            className="relative shrink-0"
            onMouseEnter={() => setActiveMenu(cat.id)}
            onMouseLeave={() => setActiveMenu(null)}
          >
            <div className="flex items-center">
              <Link
                href={`/category/${cat.slug}`}
                className="px-2.5 py-1 text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] border border-transparent transition-colors flex items-center gap-1 uppercase tracking-wider shrink-0 whitespace-nowrap"
              >
                <span>{cat.name}</span>
                {hasChildren && (
                  <ChevronDown
                    className={`w-3 h-3 text-[#666] transition-transform duration-200 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                )}
              </Link>
            </div>

            {/* Dropdown Menu for Subcategories */}
            {hasChildren && isOpen && (
              <div className="absolute top-full left-0 mt-0.5 w-64 p-2 bg-[#121212] border border-[#262626] shadow-2xl z-50 animate-in fade-in duration-150">
                <div className="p-2 border-b border-[#262626] mb-1">
                  <Link
                    href={`/category/${cat.slug}`}
                    className="text-[10px] font-bold uppercase tracking-wider text-[#E61919] hover:underline block"
                  >
                    [ TẤT CẢ // {cat.name} ({cat.article_count} BÀI) ]
                  </Link>
                </div>
                <div className="space-y-0.5">
                  {cat.children.map((sub) => (
                    <Link
                      key={sub.id}
                      href={`/category/${sub.slug}`}
                      className="flex items-center justify-between px-2.5 py-1.5 text-xs text-[#8A8A8A] hover:bg-[#1A1A1A] hover:text-[#EAEAEA] transition-colors whitespace-nowrap"
                    >
                      <span>// {sub.name}</span>
                      {sub.article_count > 0 && (
                        <span className="text-[10px] px-1 py-0.2 bg-[#0A0A0A] border border-[#262626] text-[#666]">
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
    </nav>
  );
}
