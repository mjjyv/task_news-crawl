import React from "react";
import Link from "next/link";
import { Activity, Flame, Clock, Radio, RefreshCw, ArrowRight, Filter } from "lucide-react";
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
    sort?: "latest" | "hot" | "oldest";
    min_comments?: string;
  };
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const currentPage = Number(searchParams?.page || "1") || 1;
  const sort = (searchParams?.sort as "latest" | "hot" | "oldest") || "latest";
  const minComments = searchParams?.min_comments ? Number(searchParams.min_comments) : undefined;
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
      getArticles({
        page: currentPage,
        page_size: pageSize,
        order: sort === "oldest" ? "asc" : "desc",
        sort,
        min_comments: minComments,
      }),
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
  const feedArticles = isFirstPage ? items.slice(4) : items;

  // Helper to build filter URLs
  const makeFilterUrl = (newSort: string, newMinComments?: number) => {
    const p = new URLSearchParams();
    if (newSort && newSort !== "latest") p.set("sort", newSort);
    if (newMinComments !== undefined) p.set("min_comments", newMinComments.toString());
    p.set("page", "1");
    const qs = p.toString();
    return `/${qs ? `?${qs}` : ""}`;
  };

  return (
    <div className="space-y-6">
      {/* TACTICAL FILTER HUD BAR */}
      <div className="bg-[#121212] border border-[#262626] p-3 sm:p-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Left: Sort Tabs */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-[11px] font-bold text-[#8A8A8A] uppercase tracking-wider mr-1 flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-[#E61919]" />
              FEED STREAM:
            </span>

            <Link
              href={makeFilterUrl("latest", minComments)}
              className={`px-3 py-1.5 font-mono text-xs uppercase tracking-wider border transition-colors ${
                sort === "latest"
                  ? "bg-[#E61919] text-white border-[#E61919] font-bold shadow-[0_0_8px_rgba(230,25,25,0.4)]"
                  : "bg-[#1A1A1A] text-[#8A8A8A] border-[#333] hover:text-[#EAEAEA] hover:border-[#555]"
              }`}
            >
              [ // MỚI NHẤT ]
            </Link>

            <Link
              href={makeFilterUrl("hot", minComments)}
              className={`px-3 py-1.5 font-mono text-xs uppercase tracking-wider border transition-colors flex items-center gap-1.5 ${
                sort === "hot"
                  ? "bg-[#E61919] text-white border-[#E61919] font-bold shadow-[0_0_8px_rgba(230,25,25,0.4)]"
                  : "bg-[#1A1A1A] text-[#8A8A8A] border-[#333] hover:text-[#EAEAEA] hover:border-[#555]"
              }`}
            >
              <Flame className="w-3.5 h-3.5 fill-current" />
              <span>[ 🔥 BÀI BÁO HOT (NHIỀU CMT) ]</span>
            </Link>

            <Link
              href={makeFilterUrl("oldest", minComments)}
              className={`px-3 py-1.5 font-mono text-xs uppercase tracking-wider border transition-colors ${
                sort === "oldest"
                  ? "bg-[#E61919] text-white border-[#E61919] font-bold shadow-[0_0_8px_rgba(230,25,25,0.4)]"
                  : "bg-[#1A1A1A] text-[#8A8A8A] border-[#333] hover:text-[#EAEAEA] hover:border-[#555]"
              }`}
            >
              [ // CŨ NHẤT ]
            </Link>
          </div>

          {/* Right: Min Comments Filter */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
            <span className="text-[#8A8A8A] text-[11px] uppercase mr-1 flex items-center gap-1">
              <Filter className="w-3 h-3 text-[#8A8A8A]" />
              LỌC BÌNH LUẬN:
            </span>

            <Link
              href={makeFilterUrl(sort, undefined)}
              className={`px-2 py-1 border transition-colors ${
                minComments === undefined
                  ? "bg-[#262626] text-[#EAEAEA] border-[#555] font-bold"
                  : "bg-[#171717] text-[#777] border-[#262626] hover:text-[#EAEAEA]"
              }`}
            >
              TẤT CẢ
            </Link>

            <Link
              href={makeFilterUrl(sort, 1)}
              className={`px-2 py-1 border transition-colors ${
                minComments === 1
                  ? "bg-[#262626] text-[#EAEAEA] border-[#555] font-bold"
                  : "bg-[#171717] text-[#777] border-[#262626] hover:text-[#EAEAEA]"
              }`}
            >
              &gt; 0 CMT
            </Link>

            <Link
              href={makeFilterUrl(sort, 10)}
              className={`px-2 py-1 border transition-colors ${
                minComments === 10
                  ? "bg-[#262626] text-[#EAEAEA] border-[#555] font-bold"
                  : "bg-[#171717] text-[#777] border-[#262626] hover:text-[#EAEAEA]"
              }`}
            >
              &gt; 10 CMT
            </Link>

            <Link
              href={makeFilterUrl(sort, 50)}
              className={`px-2 py-1 border transition-colors ${
                minComments === 50
                  ? "bg-[#262626] text-[#EAEAEA] border-[#555] font-bold"
                  : "bg-[#171717] text-[#777] border-[#262626] hover:text-[#EAEAEA]"
              }`}
            >
              &gt; 50 CMT
            </Link>
          </div>
        </div>

        {/* Tactical status readout */}
        <div className="mt-3 pt-2.5 border-t border-[#1F1F1F] flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-[#8A8A8A]">
          <div>
            STATUS:{" "}
            <span className="text-[#EAEAEA]">
              {sort === "hot"
                ? "SẮP XẾP THEO LƯỢNG BÌNH LUẬN CAO NHẤT (HOT FEED)"
                : sort === "oldest"
                ? "SẮP XẾP TỪ CŨ ĐẾN MỚI (ARCHIVE FEED)"
                : "DÒNG TIN MỚI NHẤT (REALTIME FEED)"}
            </span>
            {minComments !== undefined && (
              <span className="text-[#E61919] ml-2">
                [LỌC: &gt;= {minComments} BÌNH LUẬN]
              </span>
            )}
          </div>
          <div>
            TOTAL UNITS: <span className="text-[#EAEAEA] font-bold">{total}</span>
          </div>
        </div>
      </div>

      {/* Hero Section on Page 1 */}
      {isFirstPage && heroArticle && (
        <section aria-label="Tin tiêu điểm">
          <FeaturedHero article={heroArticle} />
        </section>
      )}

      {/* Sub-featured 3-Column Grid */}
      {isFirstPage && subFeatured.length > 0 && (
        <section aria-label="Tin nổi bật khác">
          <div className="flex items-center justify-between mb-3 border-b border-[#262626] pb-2">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-[#E61919]"></span>
              <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-[#EAEAEA]">
                {sort === "hot" ? "[ TOP ENGAGED DISPATCHES ]" : "[ PRIORITY WIRES ]"}
              </h2>
            </div>
            <span className="font-mono text-[10px] text-[#8A8A8A]">
              TELEMETRY // 3 UNITS
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {subFeatured.map((art) => (
              <ArticleCard key={art.id} article={art} variant="grid" />
            ))}
          </div>
        </section>
      )}

      {/* Main Content Layout: Stream + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
        {/* Left: Articles Stream */}
        <div className="lg:col-span-8 space-y-6">
          <div className="flex items-center justify-between pb-2 border-b border-[#262626]">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-[#EAEAEA] uppercase tracking-wider">
                {isFirstPage
                  ? sort === "hot"
                    ? "[ DANH SÁCH BÀI BÁO NHIỀU BÌNH LUẬN NHẤT ]"
                    : "[ DÒNG TIN ĐIỆN BÁO ]"
                  : `[ TỔNG HỢP TIN TỨC - TRANG ${currentPage} ]`}
              </span>
            </div>
            <span className="font-mono text-[10px] text-[#8A8A8A]">
              UNIT COUNT // {total}
            </span>
          </div>

          {feedArticles.length === 0 ? (
            <div className="p-12 text-center bg-[#121212] border border-[#262626] text-[#8A8A8A] font-mono">
              <p className="text-xs uppercase tracking-wider">[ NO RECORDS MATCHING CURRENT TELEMETRY PARAMETERS ]</p>
              <p className="text-[11px] mt-1 text-[#666]">
                Không có bài viết nào thỏa mãn điều kiện lọc. Thử hạ mức lọc bình luận hoặc kích hoạt cào thêm tin mới.
              </p>
              <Link
                href="/crawler"
                className="mt-4 inline-flex items-center gap-1.5 text-xs font-bold text-[#E61919] hover:underline"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>[ KÍCH HOẠT CÀO BÀI VIẾT MỚI ]</span>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {feedArticles.map((art) => (
                <ArticleCard key={art.id} article={art} variant="grid" />
              ))}
            </div>
          )}

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={total_pages}
            createPageUrl={(p) => {
              const urlParams = new URLSearchParams();
              if (sort && sort !== "latest") urlParams.set("sort", sort);
              if (minComments !== undefined) urlParams.set("min_comments", minComments.toString());
              urlParams.set("page", p.toString());
              return `/?${urlParams.toString()}`;
            }}
          />
        </div>

        {/* Right: Tactical Sidebar */}
        <aside className="lg:col-span-4 space-y-6">
          {/* Crawler Status Widget */}
          <div className="p-5 bg-[#121212] border border-[#262626]">
            <div className="flex items-center justify-between mb-3 border-b border-[#262626] pb-2">
              <h3 className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#8A8A8A] flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-[#E61919]" />
                SYS // HEALTH & TELEMETRY
              </h3>
              <span className="font-mono text-[10px] text-[#4AF626] border border-[#4AF626]/40 px-1.5 py-0.5 bg-[#4AF626]/10">
                ● NOMINAL
              </span>
            </div>

            <div className="space-y-2 font-mono text-xs text-[#8A8A8A]">
              <div className="flex justify-between py-1 border-b border-[#1A1A1A]">
                <span>TOTAL ARTICLES:</span>
                <strong className="text-[#EAEAEA]">{total}</strong>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1A1A1A]">
                <span>DATABASE:</span>
                <strong className="text-[#EAEAEA]">
                  {healthInfo?.database_connected ? "SQLITE ACTIVE" : "CHECKING"}
                </strong>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1A1A1A]">
                <span>DEDUPLICATOR:</span>
                <strong className="text-[#EAEAEA]">
                  {healthInfo?.deduplicator_type?.toUpperCase() || "IN-MEMORY SET"}
                </strong>
              </div>
            </div>

            <Link
              href="/crawler"
              className="mt-4 w-full inline-flex items-center justify-center gap-2 py-2 px-3 bg-[#1A1A1A] border border-[#333] hover:border-[#E61919] font-mono text-xs font-bold text-[#EAEAEA] hover:text-[#E61919] transition-colors"
            >
              <span>[ CRAWLER DASHBOARD ]</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Categories Quick List */}
          {categories.length > 0 && (
            <div className="p-5 bg-[#121212] border border-[#262626]">
              <h3 className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#8A8A8A] mb-3 border-b border-[#262626] pb-2">
                INDEX // CATEGORIES
              </h3>
              <div className="space-y-1">
                {categories.slice(0, 10).map((cat: any) => (
                  <Link
                    key={cat.id}
                    href={`/category/${cat.slug}`}
                    className="flex items-center justify-between py-1.5 px-2 text-xs font-mono text-[#8A8A8A] hover:bg-[#1A1A1A] hover:text-[#E61919] transition-colors border border-transparent hover:border-[#262626]"
                  >
                    <span>// {cat.name}</span>
                    <span className="text-[10px] text-[#555] bg-[#0A0A0A] border border-[#262626] px-1.5 py-0.5">
                      {cat.article_count}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Tactical Telemetry Reader Mode Notice */}
          <div className="p-4 bg-[#141414] border-l-2 border-[#E61919] font-mono text-xs text-[#8A8A8A]">
            <h4 className="font-bold text-[#EAEAEA] mb-1 uppercase tracking-wider">
              [ INTEL // READING PROTOCOL ]
            </h4>
            <p className="text-[11px] leading-relaxed text-[#777]">
              Mọi bài viết được giải mã sạch từ VnExpress, loại trừ 100% mã theo dõi và quảng cáo. Bài viết có lượt bình luận cao thể hiện mức độ quan tâm lớn của cộng đồng.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

