"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Menu, X, ChevronDown, ChevronRight, Search, Activity, Home } from "lucide-react";
import { CategoryTreeItem } from "@/lib/types";

interface MobileNavProps {
  categories: CategoryTreeItem[];
  onOpenSearch: () => void;
}

export function MobileNav({ categories, onOpenSearch }: MobileNavProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Record<number, boolean>>({});

  const toggleCategory = (id: number) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const closeDrawer = () => setIsOpen(false);

  return (
    <div className="lg:hidden">
      {/* Hamburger Trigger */}
      <button
        onClick={() => setIsOpen(true)}
        type="button"
        className="p-2 rounded-lg text-neutral-600 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
        aria-label="Mở menu"
      >
        <Menu className="w-6 h-6" />
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={closeDrawer}
        />
      )}

      {/* Drawer Panel */}
      <div
        className={`fixed top-0 left-0 bottom-0 w-80 max-w-[85vw] bg-white dark:bg-neutral-900 z-50 shadow-2xl flex flex-col transition-transform duration-300 ease-out border-r border-neutral-200 dark:border-neutral-800 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-brand-600 text-white font-extrabold flex items-center justify-center text-sm shadow">
              V
            </span>
            <span className="font-bold text-base text-neutral-900 dark:text-neutral-100">
              VnExpress Reader
            </span>
          </div>
          <button
            onClick={closeDrawer}
            type="button"
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Search Button in Mobile Drawer */}
        <div className="p-4 border-b border-neutral-100 dark:border-neutral-800">
          <button
            onClick={() => {
              closeDrawer();
              onOpenSearch();
            }}
            type="button"
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400 text-xs font-medium"
          >
            <Search className="w-4 h-4 text-neutral-400" />
            <span>Tìm kiếm tin tức nhanh...</span>
          </button>
        </div>

        {/* Categories List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
          <Link
            href="/"
            onClick={closeDrawer}
            className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <Home className="w-4 h-4 text-brand-600" />
            <span>Trang chủ</span>
          </Link>

          {categories.map((cat) => {
            const hasChildren = cat.children && cat.children.length > 0;
            const isExpanded = !!expandedCategories[cat.id];

            return (
              <div key={cat.id} className="space-y-0.5">
                <div className="flex items-center justify-between rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
                  <Link
                    href={`/category/${cat.slug}`}
                    onClick={closeDrawer}
                    className="flex-1 px-3 py-2.5 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:text-brand-600 transition-colors"
                  >
                    {cat.name}
                  </Link>

                  {hasChildren && (
                    <button
                      onClick={() => toggleCategory(cat.id)}
                      type="button"
                      className="p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                  )}
                </div>

                {/* Subcategories Accordion */}
                {hasChildren && isExpanded && (
                  <div className="pl-6 pr-2 py-1 space-y-0.5 border-l-2 border-neutral-100 dark:border-neutral-800 ml-3">
                    {cat.children.map((sub) => (
                      <Link
                        key={sub.id}
                        href={`/category/${sub.slug}`}
                        onClick={closeDrawer}
                        className="block px-3 py-2 text-xs text-neutral-600 dark:text-neutral-400 hover:text-brand-600 dark:hover:text-brand-400 rounded-lg transition-colors"
                      >
                        {sub.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-950">
          <Link
            href="/crawler"
            onClick={closeDrawer}
            className="flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors"
          >
            <span className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-600" />
              Giám sát Crawler & Dữ liệu
            </span>
            <span>&rarr;</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
