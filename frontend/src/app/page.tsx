import React from "react";
import Link from "next/link";
import { Sparkles, Newspaper, TrendingUp, RefreshCw, ArrowRight } from "lucide-react";
import { getArticles, getCategories, getCrawlerHealth } from "@/lib/api";
import {
  ArticleSummary,
  CategoryTreeItem,
  CrawlerHealthResponse,
  PaginatedResponse,
} from "@/lib/types";
import { FeaturedHero } from "@/components/FeaturedHero";
import { ArticleCard } from "@/components/ArticleCard";
import { Pagination } from "@/components/Pagination";

interface HomePageProps {
  searchParams?: {
    page?: string;
  };
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const currentPage = Number(searchParams?.page || "1") || 1;
  const pageSize = 12;

  let articlesRes: PaginatedResponse<ArticleSummary> = {
    items: [],
    total: 0,
    page: 1,
    page_size: pageSize,
    total_pages: 1,
  };
  let categories: CategoryTreeItem[] = [];
  let healthInfo: CrawlerHealthResponse | null = null;

  try {
    const [articles, cats, health] = await Promise.all([
      getArticles({ page: currentPage, page_size: pageSize, order: "desc" }),
      getCategories(true).catch(() => []),
      getCrawlerHealth().catch(() => null),
    ]);
    articlesRes = articles;
    categories = cats;
    healthInfo = health;
  } catch (error) {
    console.error("Error loading home page data:", error);
  }

  const { items, total_pages, total } = articlesRes;
  const isFirstPage = currentPage === 1;

  // Split into Hero, Sub-featured, and Feed on first page
  const heroArticle = isFirstPage && items.length > 0 ? items[0] : null;
  const subFeatured = isFirstPage && items.length > 3 ? items.slice(1, 4) : [];
  const feedArticles = isFirstPage
    ? items.slice(4)
    : items;

  return (
    <div className="space-y-8">
      {/* Hero Section on Page 1 */}
      {isFirstPage && heroArticle && (
        <section aria-label="Tin tiêu điểm">
          <FeaturedHero article={heroArticle} />
        </section>
      )}

      {/* Sub-featured 3-Column Grid */}
      {isFirstPage && subFeatured.length > 0 && (
        <section aria-label="Tin nổi bật khác">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
              Đáng chú ý hôm nay
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {subFeatured.map((art) => (
              <ArticleCard key={art.id} article={art} variant="grid" />
            ))}
          </div>
        </section>
      )}

      {/* Main Content Layout: Stream + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-4">
        {/* Left: Latest Articles Stream */}
        <div className="lg:col-span-8 space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-2">
              <Newspaper className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <h2 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
                {isFirstPage ? "Dòng tin mới nhất" : `Tin tức tổng hợp - Trang ${currentPage}`}
              </h2>
            </div>
            <span className="text-xs text-neutral-500">
              Tổng số {total} bài viết
            </span>
          </div>

          {feedArticles.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-500">
              <p>Hiện chưa có bài viết nào trong hệ thống.</p>
              <Link
                href="/crawler"
                className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Kích hoạt cào bài viết mới ngay
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {feedArticles.map((art) => (
                <ArticleCard key={art.id} article={art} variant="grid" />
              ))}
            </div>
          )}

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={total_pages}
            createPageUrl={(p) => `/?page=${p}`}
          />
        </div>

        {/* Right: Sidebar Widgets */}
        <aside className="lg:col-span-4 space-y-6">
          {/* Crawler Status Widget */}
          <div className="p-5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
                Trạng thái hệ thống
              </h3>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
                ● Đang hoạt động
              </span>
            </div>

            <div className="space-y-2 text-xs text-neutral-600 dark:text-neutral-300">
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span>Tổng số bài viết:</span>
                <strong className="text-neutral-900 dark:text-neutral-100">{total}</strong>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span>Cơ sở dữ liệu:</span>
                <strong className="text-neutral-900 dark:text-neutral-100">
                  {healthInfo?.database_connected ? "SQLite Connected" : "Đang kiểm tra"}
                </strong>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span>Bộ lọc trùng lặp:</span>
                <strong className="text-neutral-900 dark:text-neutral-100">
                  {healthInfo?.deduplicator_type || "In-Memory Set"}
                </strong>
              </div>
            </div>

            <Link
              href="/crawler"
              className="mt-4 w-full inline-flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-neutral-100 dark:bg-neutral-800 text-xs font-semibold text-neutral-800 dark:text-neutral-200 hover:bg-brand-600 hover:text-white transition-colors"
            >
              Xem chi tiết tiến trình & cào tin
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Categories Quick List */}
          {categories.length > 0 && (
            <div className="p-5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-3">
                Chuyên mục tin tức
              </h3>
              <div className="space-y-1">
                {categories.slice(0, 8).map((cat: any) => (
                  <Link
                    key={cat.id}
                    href={`/category/${cat.slug}`}
                    className="flex items-center justify-between py-1.5 px-2 rounded-lg text-xs font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
                  >
                    <span>{cat.name}</span>
                    <span className="text-[10px] text-neutral-400 bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded-full">
                      {cat.article_count} bài
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Minimalist Reader Mode Info */}
          <div className="p-5 rounded-2xl bg-brand-50 dark:bg-brand-950/40 border border-brand-100 dark:border-brand-900/50 text-xs text-brand-900 dark:text-brand-200">
            <h4 className="font-bold mb-1">💡 Trải nghiệm đọc tin sạch</h4>
            <p className="leading-relaxed opacity-90">
              Mọi bài viết trên hệ thống đã được lọc sạch mã theo dõi và quảng cáo từ trang báo gốc. Bạn có thể nhấn vào biểu tượng kính lúp hoặc phím <kbd className="px-1 py-0.5 rounded bg-white/60 dark:bg-black/40 font-mono">Ctrl + K</kbd> để tìm kiếm tin tức nhanh chóng.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
