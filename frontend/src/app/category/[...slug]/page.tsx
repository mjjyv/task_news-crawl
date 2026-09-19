import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Folder, Layers, ArrowUpDown, Clock } from "lucide-react";
import { getArticles, getCategoryBySlug } from "@/lib/api";
import {
  ArticleSummary,
  CategoryDetailResponse,
  PaginatedResponse,
} from "@/lib/types";
import { Breadcrumb } from "@/components/Breadcrumb";
import { ArticleCard } from "@/components/ArticleCard";
import { Pagination } from "@/components/Pagination";

interface CategoryPageProps {
  params: {
    slug: string[];
  };
  searchParams?: {
    page?: string;
    order?: "desc" | "asc";
    sort?: "latest" | "hot" | "oldest";
  };
}

export default async function CategoryPage({
  params,
  searchParams,
}: CategoryPageProps) {
  const fullSlug = params.slug.join("/");
  const currentPage = Number(searchParams?.page || "1") || 1;
  const sort = (searchParams?.sort as "latest" | "hot" | "oldest") || (searchParams?.order === "asc" ? "oldest" : "latest");
  const pageSize = 12;

  let categoryDetail: CategoryDetailResponse;
  try {
    categoryDetail = await getCategoryBySlug(fullSlug);
  } catch (err) {
    console.error("Failed to fetch category:", err);
    notFound();
  }

  let articlesRes: PaginatedResponse<ArticleSummary> = {
    items: [],
    total: 0,
    page: 1,
    page_size: pageSize,
    total_pages: 1,
  };

  try {
    articlesRes = await getArticles({
      category: fullSlug,
      page: currentPage,
      page_size: pageSize,
      order: sort === "oldest" ? "asc" : "desc",
      sort,
    });
  } catch (err) {
    console.error("Failed to fetch category articles:", err);
  }

  const { items, total_pages, total } = articlesRes;

  // Build breadcrumb items
  const breadcrumbItems = [];
  if (categoryDetail.parent) {
    breadcrumbItems.push({
      label: categoryDetail.parent.name,
      href: `/category/${categoryDetail.parent.slug}`,
    });
  }
  breadcrumbItems.push({
    label: categoryDetail.name,
    href: `/category/${categoryDetail.slug}`,
  });

  // Determine subcategory tabs
  const subCategories = categoryDetail.children || [];

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumb items={breadcrumbItems} />

      {/* Category Header */}
      <div className="p-5 bg-[#121212] border border-[#262626]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-[#E61919] font-mono text-[10px] font-bold uppercase tracking-wider mb-1">
              <Folder className="w-3.5 h-3.5" />
              <span>CATEGORY DISPATCH // ID #{categoryDetail.id}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#EAEAEA] font-sans tracking-tight">
              {categoryDetail.name}
            </h1>
            {categoryDetail.description && (
              <p className="mt-1 text-xs text-[#8A8A8A] max-w-2xl font-mono">
                // {categoryDetail.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Sort order toggle with Hot Feed option */}
            <div className="flex items-center bg-[#1A1A1A] border border-[#333] p-1 font-mono text-xs">
              <Link
                href={`/category/${fullSlug}?page=1&sort=latest`}
                className={`px-2.5 py-1 uppercase tracking-wider transition-colors ${
                  sort === "latest"
                    ? "bg-[#E61919] text-white font-bold"
                    : "text-[#8A8A8A] hover:text-[#EAEAEA]"
                }`}
              >
                MỚI NHẤT
              </Link>
              <Link
                href={`/category/${fullSlug}?page=1&sort=hot`}
                className={`px-2.5 py-1 uppercase tracking-wider transition-colors flex items-center gap-1 ${
                  sort === "hot"
                    ? "bg-[#E61919] text-white font-bold"
                    : "text-[#8A8A8A] hover:text-[#EAEAEA]"
                }`}
              >
                <span className="text-[#E61919] group-hover:text-white">🔥</span>
                HOT
              </Link>
              <Link
                href={`/category/${fullSlug}?page=1&sort=oldest`}
                className={`px-2.5 py-1 uppercase tracking-wider transition-colors ${
                  sort === "oldest"
                    ? "bg-[#E61919] text-white font-bold"
                    : "text-[#8A8A8A] hover:text-[#EAEAEA]"
                }`}
              >
                CŨ NHẤT
              </Link>
            </div>
          </div>
        </div>

        {/* Sub-category Tabs (if available) */}
        {subCategories.length > 0 && (
          <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#1F1F1F] overflow-x-auto pb-1 font-mono text-xs">
            <span className="text-[10px] text-[#666] shrink-0 uppercase tracking-wider">
              SUB-NODES:
            </span>
            <Link
              href={`/category/${categoryDetail.slug}`}
              className="px-2 py-0.5 border border-[#E61919] bg-[#E61919] text-white font-bold text-[10px] shrink-0 uppercase"
            >
              [ TẤT CẢ // {categoryDetail.article_count} ]
            </Link>
            {subCategories.map((sub) => (
              <Link
                key={sub.id}
                href={`/category/${sub.slug}`}
                className="px-2 py-0.5 border border-[#333] bg-[#1A1A1A] hover:border-[#555] text-[#8A8A8A] hover:text-[#EAEAEA] text-[10px] shrink-0 uppercase transition-colors"
              >
                [ {sub.name} ]
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Articles Count info */}
      <div className="flex items-center justify-between font-mono text-[10px] text-[#8A8A8A] border-b border-[#262626] pb-2">
        <span>
          TELEMETRY // DISPLAYING <strong>{items.length}</strong> / <strong>{total}</strong> UNITS
        </span>
        <span>PAGE {currentPage} / {total_pages || 1}</span>
      </div>

      {/* Articles Grid */}
      {items.length === 0 ? (
        <div className="py-16 text-center bg-[#121212] border border-[#262626] text-[#8A8A8A] font-mono">
          <p className="text-xs uppercase tracking-wider">[ NO TELEMETRY FOUND IN THIS SECTOR ]</p>
          <Link
            href="/crawler"
            className="mt-3 inline-block font-mono text-xs font-bold text-[#E61919] hover:underline"
          >
            [ KÍCH HOẠT CÀO BÀI VIẾT CHO CHUYÊN MỤC ] &rarr;
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((article) => (
            <ArticleCard key={article.id} article={article} variant="grid" />
          ))}
        </div>
      )}

      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={total_pages}
        createPageUrl={(p) => `/category/${fullSlug}?page=${p}&sort=${sort}`}
      />
    </div>
  );
}
