"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, Filter, CheckSquare, Square, Clock, Loader2, FileQuestion, ArrowRight } from "lucide-react";
import { searchArticles, getCategories } from "@/lib/api";
import { SearchResultItem, CategoryTreeItem } from "@/lib/types";
import { formatDateVi } from "@/lib/utils";
import { Pagination } from "@/components/Pagination";

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialQuery = searchParams.get("q") || "";
  const initialExactAccent = searchParams.get("exact_accent") === "true";
  const initialCategory = searchParams.get("category") || "";
  const initialPage = Number(searchParams.get("page") || "1") || 1;

  const [query, setQuery] = useState(initialQuery);
  const [exactAccent, setExactAccent] = useState(initialExactAccent);
  const [category, setCategory] = useState(initialCategory);
  const [categories, setCategories] = useState<CategoryTreeItem[]>([]);

  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // Fetch category list for filter dropdown
  useEffect(() => {
    getCategories(false)
      .then((data) => setCategories(data))
      .catch(() => {});
  }, []);

  // Sync state with URL params
  useEffect(() => {
    const q = searchParams.get("q") || "";
    const ea = searchParams.get("exact_accent") === "true";
    const cat = searchParams.get("category") || "";
    const p = Number(searchParams.get("page") || "1") || 1;

    setQuery(q);
    setExactAccent(ea);
    setCategory(cat);

    if (q.trim()) {
      executeSearch(q, ea, cat, p);
    } else {
      setResults([]);
      setTotal(0);
      setTotalPages(1);
      setSearched(false);
    }
  }, [searchParams]);

  const executeSearch = async (
    q: string,
    ea: boolean,
    cat: string,
    p: number
  ) => {
    setLoading(true);
    setSearched(true);
    try {
      const res = await searchArticles({
        q: q.trim(),
        exact_accent: ea,
        category: cat || undefined,
        page: p,
        page_size: 10,
      });
      setResults(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error("Search failed:", err);
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const params = new URLSearchParams();
    params.set("q", query.trim());
    if (exactAccent) params.set("exact_accent", "true");
    if (category) params.set("category", category);
    params.set("page", "1");

    router.push(`/search?${params.toString()}`);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Search Header */}
      <div className="text-center py-4">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-neutral-900 dark:text-neutral-100 mb-2">
          Tìm kiếm bài viết
        </h1>
        <p className="text-sm text-neutral-500">
          Hỗ trợ tìm kiếm thông minh tiếng Việt cả có dấu và không dấu
        </p>
      </div>

      {/* Search Box Card */}
      <div className="p-4 sm:p-6 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-md">
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Nhập từ khóa tìm kiếm (vd: trí tuệ nhân tạo, ngủ, hà nội, bão số 3...)"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/80 border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm sm:text-base"
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold text-sm transition-colors flex items-center gap-2 shrink-0 shadow-sm"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span>Tìm kiếm</span>
            </button>
          </div>

          {/* Filters Row */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 text-xs">
            {/* Exact Accent Toggle */}
            <label className="inline-flex items-center gap-2 cursor-pointer text-neutral-700 dark:text-neutral-300 select-none">
              <input
                type="checkbox"
                checked={exactAccent}
                onChange={(e) => setExactAccent(e.target.checked)}
                className="sr-only"
              />
              {exactAccent ? (
                <CheckSquare className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0" />
              ) : (
                <Square className="w-4 h-4 text-neutral-400 shrink-0" />
              )}
              <span>
                <strong>Chỉ tìm kiếm có dấu chính xác</strong> (exact_accent=true)
              </span>
            </label>

            {/* Category Dropdown Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-neutral-400" />
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="py-1.5 px-3 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 text-xs focus:outline-none"
              >
                <option value="">Tất cả chuyên mục</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.slug}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </form>
      </div>

      {/* Results Header */}
      {searched && (
        <div className="flex items-center justify-between text-xs text-neutral-500 px-2">
          <span>
            Tìm thấy <strong className="text-neutral-900 dark:text-neutral-100">{total}</strong> bài viết phù hợp
            {exactAccent && (
              <span className="ml-1.5 px-2 py-0.5 rounded bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 font-medium">
                Khớp có dấu
              </span>
            )}
          </span>
          <span>Trang {initialPage} / {totalPages || 1}</span>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center">
            <Loader2 className="w-8 h-8 mx-auto animate-spin text-brand-600 mb-2" />
            <p className="text-sm text-neutral-400">Đang tìm kiếm dữ liệu...</p>
          </div>
        ) : searched && results.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-400">
            <FileQuestion className="w-10 h-10 mx-auto mb-3 text-neutral-300 dark:text-neutral-700" />
            <h3 className="text-base font-bold text-neutral-700 dark:text-neutral-300 mb-1">
              Không tìm thấy kết quả phù hợp
            </h3>
            <p className="text-xs max-w-md mx-auto">
              Không có bài viết nào chứa từ khóa &quot;{query}&quot;. Bạn có thể thử tìm từ khóa khác hoặc tắt tùy chọn &quot;Chỉ tìm kiếm có dấu chính xác&quot;.
            </p>
          </div>
        ) : (
          results.map((item) => {
            const timeFormatted = formatDateVi(item.published_at);
            return (
              <article
                key={item.id}
                className="p-5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 hover:shadow-md transition-all flex flex-col sm:flex-row gap-4 group"
              >
                {item.thumbnail_url && (
                  <Link
                    href={`/article/${item.id}`}
                    className="sm:w-44 h-32 shrink-0 rounded-xl overflow-hidden bg-neutral-100 dark:bg-neutral-800 relative block"
                  >
                    <img
                      src={item.thumbnail_url}
                      alt={item.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  </Link>
                )}

                <div className="flex-1 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      {item.category && (
                        <span className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                          {item.category.name}
                        </span>
                      )}
                    </div>

                    <Link href={`/article/${item.id}`}>
                      <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors line-clamp-2">
                        {item.title}
                      </h3>
                    </Link>

                    {item.snippet ? (
                      <p
                        className="mt-2 text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2 leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: item.snippet }}
                      />
                    ) : item.description ? (
                      <p className="mt-2 text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2 leading-relaxed">
                        {item.description}
                      </p>
                    ) : null}
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-neutral-100 dark:border-neutral-800/60 text-xs text-neutral-400">
                    <div className="flex items-center gap-3">
                      {timeFormatted && (
                        <span className="inline-flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {timeFormatted}
                        </span>
                      )}
                      {item.author && <span>{item.author}</span>}
                    </div>

                    <Link
                      href={`/article/${item.id}`}
                      className="inline-flex items-center gap-1 font-semibold text-brand-600 dark:text-brand-400 hover:underline"
                    >
                      Đọc tiếp
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              </article>
            );
          })
        )}
      </div>

      {/* Search Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={initialPage}
          totalPages={totalPages}
          createPageUrl={(p) => {
            const params = new URLSearchParams(searchParams.toString());
            params.set("page", p.toString());
            return `/search?${params.toString()}`;
          }}
        />
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <React.Suspense
      fallback={
        <div className="p-12 text-center text-sm text-neutral-400">
          Đang tải trang tìm kiếm...
        </div>
      }
    >
      <SearchContent />
    </React.Suspense>
  );
}
