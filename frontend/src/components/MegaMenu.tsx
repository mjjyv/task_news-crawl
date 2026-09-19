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
    <nav className="hidden lg:flex items-center space-x-1 text-sm font-medium">
      <Link
        href="/"
        className="px-3 py-2 rounded-lg text-neutral-700 dark:text-neutral-200 hover:text-brand-600 dark:hover:text-brand-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
      >
        Trang chủ
      </Link>

      {categories.map((cat) => {
        const hasChildren = cat.children && cat.children.length > 0;
        const isOpen = activeMenu === cat.id;

        return (
          <div
            key={cat.id}
            className="relative"
            onMouseEnter={() => setActiveMenu(cat.id)}
            onMouseLeave={() => setActiveMenu(null)}
          >
            <div className="flex items-center">
              <Link
                href={`/category/${cat.slug}`}
                className="px-3 py-2 rounded-lg text-neutral-700 dark:text-neutral-200 hover:text-brand-600 dark:hover:text-brand-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors flex items-center gap-1"
              >
                <span>{cat.name}</span>
                {hasChildren && (
                  <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform duration-200 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                )}
              </Link>
            </div>

            {/* Dropdown Menu for Subcategories */}
            {hasChildren && isOpen && (
              <div className="absolute top-full left-0 mt-1 w-64 p-2 bg-white dark:bg-neutral-900 rounded-xl shadow-xl border border-neutral-200 dark:border-neutral-800 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="p-2 border-b border-neutral-100 dark:border-neutral-800 mb-1">
                  <Link
                    href={`/category/${cat.slug}`}
                    className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 hover:underline block"
                  >
                    Xem tất cả {cat.name} ({cat.article_count} bài)
                  </Link>
                </div>
                <div className="space-y-0.5">
                  {cat.children.map((sub) => (
                    <Link
                      key={sub.id}
                      href={`/category/${sub.slug}`}
                      className="flex items-center justify-between px-3 py-2 rounded-lg text-xs text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
                    >
                      <span>{sub.name}</span>
                      {sub.article_count > 0 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-400">
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
