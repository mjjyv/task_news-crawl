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
    <nav className="flex items-center justify-center gap-1.5 my-8 font-mono text-xs" aria-label="Phân trang">
      {/* Prev Button */}
      {currentPage > 1 ? (
        <Link
          href={createPageUrl(currentPage - 1)}
          className="inline-flex items-center justify-center px-3 py-2 border border-[#333] bg-[#141414] text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] transition-colors"
          aria-label="Trang trước"
        >
          <ChevronLeft className="w-3.5 h-3.5 mr-1 text-[#8A8A8A]" />
          [ TRƯỚC ]
        </Link>
      ) : (
        <span className="inline-flex items-center justify-center px-3 py-2 border border-[#222] bg-[#0E0E0E] text-[#444] cursor-not-allowed">
          <ChevronLeft className="w-3.5 h-3.5 mr-1" />
          [ TRƯỚC ]
        </span>
      )}

      {/* Page Numbers */}
      <div className="flex items-center gap-1">
        {pages.map((p, idx) => {
          if (p === "...") {
            return (
              <span key={`dots-${idx}`} className="px-2 py-1 text-[#555]">
                //
              </span>
            );
          }
          const isCurrent = p === currentPage;
          return isCurrent ? (
            <span
              key={p}
              className="inline-flex items-center justify-center w-8 h-8 font-bold bg-[#E61919] text-white border border-[#E61919] shadow-[0_0_8px_rgba(230,25,25,0.4)]"
              aria-current="page"
            >
              {String(p).padStart(2, "0")}
            </span>
          ) : (
            <Link
              key={p}
              href={createPageUrl(p as number)}
              className="inline-flex items-center justify-center w-8 h-8 border border-[#333] bg-[#141414] text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] transition-colors"
            >
              {String(p).padStart(2, "0")}
            </Link>
          );
        })}
      </div>

      {/* Next Button */}
      {currentPage < totalPages ? (
        <Link
          href={createPageUrl(currentPage + 1)}
          className="inline-flex items-center justify-center px-3 py-2 border border-[#333] bg-[#141414] text-[#8A8A8A] hover:text-[#EAEAEA] hover:border-[#E61919] transition-colors"
          aria-label="Trang sau"
        >
          [ SAU ]
          <ChevronRight className="w-3.5 h-3.5 ml-1 text-[#8A8A8A]" />
        </Link>
      ) : (
        <span className="inline-flex items-center justify-center px-3 py-2 border border-[#222] bg-[#0E0E0E] text-[#444] cursor-not-allowed">
          [ SAU ]
          <ChevronRight className="w-3.5 h-3.5 ml-1" />
        </span>
      )}
    </nav>
  );
}
