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
  };
}

export default async function CategoryPage({
  params,
  searchParams,
}: CategoryPageProps) {
  const fullSlug = params.slug.join("/");
  const currentPage = Number(searchParams?.page || "1") || 1;
  const order = searchParams?.order === "asc" ? "asc" : "desc";
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
      order,
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
      <div className="pb-6 border-b border-neutral-200 dark:border-neutral-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-brand-600 dark:text-brand-400 text-xs font-bold uppercase tracking-wider mb-1">
              <Folder className="w-4 h-4" />
              <span>Chuyên mục tin tức</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-neutral-900 dark:text-neutral-100">
              {categoryDetail.name}
            </h1>
            {categoryDetail.description && (
              <p className="mt-1 text-sm text-neutral-500 max-w-2xl">
                {categoryDetail.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Sort order toggle */}
            <div className="flex items-center bg-neutral-100 dark:bg-neutral-800 p-1 rounded-xl text-xs">
              <Link
                href={`/category/${fullSlug}?page=1&order=desc`}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  order === "desc"
                    ? "bg-white dark:bg-neutral-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900"
                }`}
              >
                Mới nhất
              </Link>
              <Link
                href={`/category/${fullSlug}?page=1&order=asc`}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  order === "asc"
                    ? "bg-white dark:bg-neutral-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900"
                }`}
              >
                Cũ nhất
              </Link>
            </div>
          </div>
        </div>

        {/* Sub-category Tabs (if available) */}
        {subCategories.length > 0 && (
          <div className="flex items-center gap-2 mt-5 overflow-x-auto pb-1 scrollbar-none">
            <span className="text-xs font-semibold text-neutral-400 shrink-0 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5" />
              Nhánh con:
            </span>
            <Link
              href={`/category/${categoryDetail.slug}`}
              className="px-3 py-1 text-xs rounded-full bg-brand-600 text-white font-medium shrink-0"
            >
              Tất cả ({categoryDetail.article_count})
            </Link>
            {subCategories.map((sub) => (
              <Link
                key={sub.id}
                href={`/category/${sub.slug}`}
                className="px-3 py-1 text-xs rounded-full bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 transition-colors shrink-0"
              >
                {sub.name}
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Articles Count info */}
      <div className="flex items-center justify-between text-xs text-neutral-500">
        <span>
          Hiển thị <strong>{items.length}</strong> / <strong>{total}</strong> bài viết
        </span>
        <span>Trang {currentPage} / {total_pages || 1}</span>
      </div>

      {/* Articles Grid */}
      {items.length === 0 ? (
        <div className="py-16 text-center rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-500">
          <p className="text-sm">Chưa có bài viết nào trong chuyên mục này.</p>
          <Link
            href="/crawler"
            className="mt-3 inline-block text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline"
          >
            Kích hoạt cào bài viết cho chuyên mục &rarr;
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((article) => (
            <ArticleCard key={article.id} article={article} variant="grid" />
          ))}
        </div>
      )}

      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={total_pages}
        createPageUrl={(p) => `/category/${fullSlug}?page=${p}&order=${order}`}
      />
    </div>
  );
}
