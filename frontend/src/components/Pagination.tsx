import React from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  createPageUrl: (page: number) => string;
}

export function Pagination({ currentPage, totalPages, createPageUrl }: PaginationProps) {
  if (totalPages <= 1) return null;

  // Generate page numbers to show (e.g. 1, 2, 3, ... 10)
  const getPages = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push("...");

      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) pages.push(i);

      if (currentPage < totalPages - 2) pages.push("...");
      pages.push(totalPages);
    }
    return pages;
  };

  const pages = getPages();

  return (
    <nav className="flex items-center justify-center gap-1.5 my-8" aria-label="Phân trang">
      {/* Prev Button */}
      {currentPage > 1 ? (
        <Link
          href={createPageUrl(currentPage - 1)}
          className="inline-flex items-center justify-center px-3 py-2 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          aria-label="Trang trước"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Trước
        </Link>
      ) : (
        <span className="inline-flex items-center justify-center px-3 py-2 text-xs font-medium rounded-lg border border-neutral-200/50 dark:border-neutral-800/50 text-neutral-400 dark:text-neutral-600 cursor-not-allowed">
          <ChevronLeft className="w-4 h-4 mr-1" />
          Trước
        </span>
      )}

      {/* Page Numbers */}
      <div className="flex items-center gap-1">
        {pages.map((p, idx) => {
          if (p === "...") {
            return (
              <span key={`dots-${idx}`} className="px-2 py-1 text-xs text-neutral-400">
                ...
              </span>
            );
          }
          const isCurrent = p === currentPage;
          return isCurrent ? (
            <span
              key={p}
              className="inline-flex items-center justify-center w-8 h-8 text-xs font-semibold rounded-lg bg-brand-600 text-white shadow-sm"
              aria-current="page"
            >
              {p}
            </span>
          ) : (
            <Link
              key={p}
              href={createPageUrl(p as number)}
              className="inline-flex items-center justify-center w-8 h-8 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            >
              {p}
            </Link>
          );
        })}
      </div>

      {/* Next Button */}
      {currentPage < totalPages ? (
        <Link
          href={createPageUrl(currentPage + 1)}
          className="inline-flex items-center justify-center px-3 py-2 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          aria-label="Trang sau"
        >
          Sau
          <ChevronRight className="w-4 h-4 ml-1" />
        </Link>
      ) : (
        <span className="inline-flex items-center justify-center px-3 py-2 text-xs font-medium rounded-lg border border-neutral-200/50 dark:border-neutral-800/50 text-neutral-400 dark:text-neutral-600 cursor-not-allowed">
          Sau
          <ChevronRight className="w-4 h-4 ml-1" />
        </span>
      )}
    </nav>
  );
}
