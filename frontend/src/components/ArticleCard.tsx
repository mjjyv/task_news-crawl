import React from "react";
import Link from "next/link";
import { Clock, User } from "lucide-react";
import { ArticleSummary } from "@/lib/types";
import { formatDateVi } from "@/lib/utils";

interface ArticleCardProps {
  article: ArticleSummary;
  variant?: "grid" | "list" | "compact";
}

export function ArticleCard({ article, variant = "grid" }: ArticleCardProps) {
  const categoryName = article.category?.name || "Tin tức";
  const categorySlug = article.category?.slug;
  const timeFormatted = formatDateVi(article.published_at);

  if (variant === "compact") {
    return (
      <article className="group flex items-start gap-3 py-2.5 border-b border-neutral-100 dark:border-neutral-800 last:border-0">
        {article.thumbnail_url && (
          <Link
            href={`/article/${article.id}`}
            className="w-16 h-16 shrink-0 rounded-lg overflow-hidden bg-neutral-100 dark:bg-neutral-800 relative"
          >
            <img
              src={article.thumbnail_url}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          </Link>
        )}
        <div className="flex-1 min-w-0">
          <Link href={`/article/${article.id}`}>
            <h4 className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 group-hover:text-brand-600 dark:group-hover:text-brand-400 line-clamp-2 transition-colors">
              {article.title}
            </h4>
          </Link>
          <div className="flex items-center gap-2 mt-1 text-[11px] text-neutral-400">
            {timeFormatted && <span>{timeFormatted}</span>}
          </div>
        </div>
      </article>
    );
  }

  if (variant === "list") {
    return (
      <article className="group flex flex-col sm:flex-row gap-4 p-4 rounded-xl bg-white dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 hover:shadow-md dark:hover:shadow-neutral-950/50 transition-all">
        {article.thumbnail_url && (
          <Link
            href={`/article/${article.id}`}
            className="sm:w-52 h-36 shrink-0 rounded-lg overflow-hidden bg-neutral-100 dark:bg-neutral-800 relative"
          >
            <img
              src={article.thumbnail_url}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          </Link>
        )}

        <div className="flex-1 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              {categorySlug ? (
                <Link
                  href={`/category/${categorySlug}`}
                  className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400 hover:underline"
                >
                  {categoryName}
                </Link>
              ) : (
                <span className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                  {categoryName}
                </span>
              )}
            </div>

            <Link href={`/article/${article.id}`}>
              <h3 className="text-base sm:text-lg font-bold text-neutral-900 dark:text-neutral-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 line-clamp-2 transition-colors">
                {article.title}
              </h3>
            </Link>

            {article.description && (
              <p className="mt-2 text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2 leading-relaxed">
                {article.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3 mt-3 text-xs text-neutral-400">
            {timeFormatted && (
              <span className="inline-flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {timeFormatted}
              </span>
            )}
            {article.author && (
              <span className="inline-flex items-center gap-1">
                <User className="w-3.5 h-3.5" />
                {article.author}
              </span>
            )}
          </div>
        </div>
      </article>
    );
  }

  // Default "grid" card
  return (
    <article className="group flex flex-col rounded-xl overflow-hidden bg-white dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 hover:shadow-lg dark:hover:shadow-neutral-950/50 transition-all">
      {article.thumbnail_url ? (
        <Link
          href={`/article/${article.id}`}
          className="w-full aspect-[16/10] overflow-hidden bg-neutral-100 dark:bg-neutral-800 relative block"
        >
          <img
            src={article.thumbnail_url}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        </Link>
      ) : (
        <div className="w-full aspect-[16/10] bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-neutral-400 text-xs">
          Không có hình ảnh
        </div>
      )}

      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            {categorySlug ? (
              <Link
                href={`/category/${categorySlug}`}
                className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400 hover:underline"
              >
                {categoryName}
              </Link>
            ) : (
              <span className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                {categoryName}
              </span>
            )}
          </div>

          <Link href={`/article/${article.id}`}>
            <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 line-clamp-2 transition-colors">
              {article.title}
            </h3>
          </Link>

          {article.description && (
            <p className="mt-2 text-xs text-neutral-600 dark:text-neutral-400 line-clamp-3 leading-relaxed">
              {article.description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3 mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800/60 text-xs text-neutral-400">
          {timeFormatted && (
            <span className="inline-flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {timeFormatted}
            </span>
          )}
          {article.author && (
            <span className="inline-flex items-center gap-1 truncate max-w-[120px]">
              <User className="w-3.5 h-3.5" />
              {article.author}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}
