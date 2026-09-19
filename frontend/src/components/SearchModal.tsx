"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, X, Loader2, ArrowRight, Sparkles, CheckSquare, Square } from "lucide-react";
import { useDebounce } from "@/hooks/useDebounce";
import { searchArticles } from "@/lib/api";
import { SearchResultItem } from "@/lib/types";

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [exactAccent, setExactAccent] = useState(false);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState<number | null>(null);

  const debouncedQuery = useDebounce(query, 180);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
      setResults([]);
      setTotalCount(null);
    }
  }, [isOpen]);

  // Execute live search
  useEffect(() => {
    let active = true;
    if (!debouncedQuery.trim()) {
      setResults([]);
      setTotalCount(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    searchArticles({
      q: debouncedQuery.trim(),
      exact_accent: exactAccent,
      page: 1,
      page_size: 5,
    })
      .then((res) => {
        if (!active) return;
        setResults(res.items);
        setTotalCount(res.total);
      })
      .catch(() => {
        if (!active) return;
        setResults([]);
        setTotalCount(0);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [debouncedQuery, exactAccent]);

  // Handle Enter key to redirect to full search page
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && query.trim()) {
      onClose();
      router.push(`/search?q=${encodeURIComponent(query.trim())}&exact_accent=${exactAccent}`);
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="w-full max-w-2xl bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-neutral-200 dark:border-neutral-800 overflow-hidden flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Header */}
        <div className="flex items-center px-4 py-3 border-b border-neutral-200 dark:border-neutral-800 gap-3">
          <Search className="w-5 h-5 text-neutral-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Tìm kiếm tin tức (vd: trí tuệ nhân tạo, ngủ, hà nội...)"
            className="flex-1 bg-transparent border-0 focus:outline-none text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 text-base"
          />
          {loading && <Loader2 className="w-5 h-5 text-brand-500 animate-spin shrink-0" />}
          <button
            onClick={onClose}
            className="p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Filter Bar inside modal */}
        <div className="px-4 py-2 bg-neutral-50 dark:bg-neutral-950/60 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400">
          <button
            type="button"
            onClick={() => setExactAccent(!exactAccent)}
            className="inline-flex items-center gap-1.5 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
          >
            {exactAccent ? (
              <CheckSquare className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            ) : (
              <Square className="w-4 h-4 text-neutral-400" />
            )}
            <span>Chỉ tìm kiếm có dấu chính xác (exact_accent)</span>
          </button>

          <span className="hidden sm:inline text-neutral-400">
            Nhấn <kbd className="px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-800 rounded font-mono">Enter</kbd> để xem tất cả
          </span>
        </div>

        {/* Results List */}
        <div className="overflow-y-auto p-3 space-y-2 flex-1">
          {query.trim() === "" ? (
            <div className="py-12 text-center text-neutral-400 text-sm">
              <Sparkles className="w-8 h-8 mx-auto mb-2 text-brand-500/50" />
              <p>Gõ từ khóa để bắt đầu tìm kiếm nhanh chóng</p>
              <div className="flex flex-wrap justify-center gap-1.5 mt-3">
                {["Trí tuệ nhân tạo", "Công nghệ", "Hà Nội", "Smartwatch"].map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setQuery(tag)}
                    className="px-2.5 py-1 text-xs rounded-full bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300"
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          ) : results.length === 0 && !loading ? (
            <div className="py-10 text-center text-neutral-400 text-sm">
              Không tìm thấy kết quả nào phù hợp với &quot;{query}&quot;.
              {exactAccent && (
                <p className="mt-1 text-xs text-neutral-500">
                  Thử tắt tuỳ chọn &quot;Chỉ tìm kiếm có dấu chính xác&quot; để tìm mở rộng.
                </p>
              )}
            </div>
          ) : (
            results.map((item) => (
              <Link
                key={item.id}
                href={`/article/${item.id}`}
                onClick={onClose}
                className="group flex items-start gap-3 p-2.5 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800/70 transition-colors"
              >
                {item.thumbnail_url ? (
                  <img
                    src={item.thumbnail_url}
                    alt={item.title}
                    className="w-16 h-16 object-cover rounded-lg shrink-0 bg-neutral-200 dark:bg-neutral-800"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center shrink-0 text-neutral-400 text-xs">
                    No img
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  {item.category && (
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                      {item.category.name}
                    </span>
                  )}
                  <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 line-clamp-1">
                    {item.title}
                  </h4>
                  {item.snippet ? (
                    <p
                      className="text-xs text-neutral-500 dark:text-neutral-400 line-clamp-2 mt-0.5"
                      dangerouslySetInnerHTML={{ __html: item.snippet }}
                    />
                  ) : item.description ? (
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 line-clamp-2 mt-0.5">
                      {item.description}
                    </p>
                  ) : null}
                </div>
              </Link>
            ))
          )}
        </div>

        {/* Modal Footer */}
        {totalCount !== null && totalCount > 0 && (
          <div className="px-4 py-2.5 border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-950 flex items-center justify-between">
            <span className="text-xs text-neutral-500">
              Tìm thấy <strong className="text-neutral-800 dark:text-neutral-200">{totalCount}</strong> kết quả
            </span>
            <Link
              href={`/search?q=${encodeURIComponent(query.trim())}&exact_accent=${exactAccent}`}
              onClick={onClose}
              className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline"
            >
              Xem tất cả kết quả
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
