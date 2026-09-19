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
      <div className="p-4 sm:p-6 bg-[#121212] border border-[#262626]">
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8A8A8A]" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Nhập từ khóa tìm kiếm (vd: trí tuệ nhân tạo, ngủ, hà nội, bão số 3...)"
                className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-[#333] text-[#EAEAEA] placeholder-[#555] focus:outline-none focus:border-[#E61919] font-mono text-xs sm:text-sm"
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-2.5 bg-[#E61919] hover:bg-[#cc1414] disabled:opacity-50 text-white font-mono font-bold text-xs uppercase tracking-wider transition-colors flex items-center gap-2 shrink-0 border border-[#E61919]"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Search className="w-3.5 h-3.5" />
              )}
              <span>[ TÌM KIẾM ]</span>
            </button>
          </div>

          {/* Filters Row */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 font-mono text-xs">
            {/* Exact Accent Toggle */}
            <label className="inline-flex items-center gap-2 cursor-pointer text-[#8A8A8A] hover:text-[#EAEAEA] select-none">
              <input
                type="checkbox"
                checked={exactAccent}
                onChange={(e) => setExactAccent(e.target.checked)}
                className="sr-only"
              />
              {exactAccent ? (
                <CheckSquare className="w-4 h-4 text-[#E61919] shrink-0" />
              ) : (
                <Square className="w-4 h-4 text-[#555] shrink-0" />
              )}
              <span>
                <strong>Chỉ tìm kiếm có dấu chính xác</strong> [exact_accent=true]
              </span>
            </label>

            {/* Category Dropdown Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-3 h-3 text-[#8A8A8A]" />
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="py-1.5 px-3 bg-[#1A1A1A] border border-[#333] text-[#EAEAEA] text-xs font-mono focus:outline-none focus:border-[#E61919]"
              >
                <option value="">-- TẤT CẢ CHUYÊN MỤC --</option>
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
        <div className="flex items-center justify-between font-mono text-[10px] text-[#8A8A8A] px-1 border-b border-[#262626] pb-2">
          <span>
            KẾT QUẢ: TÌM THẤY <strong className="text-[#EAEAEA]">{total}</strong> BÀI VIẾT
            {exactAccent && (
              <span className="ml-2 px-1.5 py-0.5 bg-[#E61919]/20 border border-[#E61919] text-[#E61919] font-bold">
                KHỚP CÓ DẤU
              </span>
            )}
          </span>
          <span>TRANG {initialPage} / {totalPages || 1}</span>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center font-mono">
            <Loader2 className="w-6 h-6 mx-auto animate-spin text-[#E61919] mb-2" />
            <p className="text-xs text-[#8A8A8A] uppercase">[ QUERYING DATABASE MATRIX... ]</p>
          </div>
        ) : searched && results.length === 0 ? (
          <div className="p-12 text-center bg-[#121212] border border-[#262626] text-[#8A8A8A] font-mono">
            <FileQuestion className="w-8 h-8 mx-auto mb-2 text-[#555]" />
            <h3 className="text-xs font-bold text-[#EAEAEA] mb-1 uppercase tracking-wider">
              [ KHÔNG TÌM THẤY KẾT QUẢ PHÙ HỢP ]
            </h3>
            <p className="text-[11px] max-w-md mx-auto text-[#666]">
              Không có bài viết nào chứa từ khóa &quot;{query}&quot;. Thử tìm từ khóa khác hoặc tắt tùy chọn &quot;Chỉ tìm kiếm có dấu chính xác&quot;.
            </p>
          </div>
        ) : (
          results.map((item) => {
            const timeFormatted = formatDateVi(item.published_at);
            const cCount = item.comment_count ?? 0;
            const isHot = cCount >= 10;
            return (
              <article
                key={item.id}
                className="p-4 bg-[#121212] border border-[#262626] hover:border-[#E61919] transition-all flex flex-col sm:flex-row gap-4 group"
              >
                {item.thumbnail_url && (
                  <Link
                    href={`/article/${item.id}`}
                    className="sm:w-44 h-32 shrink-0 bg-[#1A1A1A] border border-[#262626] overflow-hidden relative block"
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
                    <div className="flex flex-wrap items-center gap-2 mb-1.5 font-mono text-[10px]">
                      {item.category && (
                        <span className="font-bold uppercase tracking-wider text-[#8A8A8A] border border-[#262626] px-1.5 py-0.5 bg-[#0A0A0A]">
                          [ {item.category.name} ]
                        </span>
                      )}

                      {/* Comment Count Telemetry Badge */}
                      {isHot ? (
                        <span className="px-1.5 py-0.5 bg-[#E61919] text-white font-bold tracking-wider border border-[#E61919]">
                          🔥 HOT // {cCount} CMT
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 bg-[#1A1A1A] text-[#8A8A8A] border border-[#333]">
                          CMT // {String(cCount).padStart(3, "0")}
                        </span>
                      )}

                      <span className="text-[#555] ml-auto">ID #{item.id}</span>
                    </div>

                    <Link href={`/article/${item.id}`}>
                      <h3 className="text-base font-bold text-[#EAEAEA] group-hover:text-[#E61919] transition-colors line-clamp-2 font-sans">
                        {item.title}
                      </h3>
                    </Link>

                    {item.snippet ? (
                      <p
                        className="mt-2 text-xs text-[#8A8A8A] line-clamp-2 leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: item.snippet }}
                      />
                    ) : item.description ? (
                      <p className="mt-2 text-xs text-[#8A8A8A] line-clamp-2 leading-relaxed">
                        {item.description}
                      </p>
                    ) : null}
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-[#1F1F1F] font-mono text-[10px] text-[#8A8A8A]">
                    <div className="flex items-center gap-3">
                      {timeFormatted && (
                        <span className="inline-flex items-center gap-1">
                          <Clock className="w-3 h-3 text-[#666]" />
                          {timeFormatted}
                        </span>
                      )}
                      {item.author && <span>// {item.author}</span>}
                    </div>

                    <Link
                      href={`/article/${item.id}`}
                      className="inline-flex items-center gap-1 font-bold text-[#E61919] hover:underline"
                    >
                      <span>[ ĐỌC BÀI VIẾT ]</span>
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
