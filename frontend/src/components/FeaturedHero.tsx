import React from "react";
import Link from "next/link";
import { Clock, User, Sparkles } from "lucide-react";
import { ArticleSummary } from "@/lib/types";
import { formatDateVi } from "@/lib/utils";

interface FeaturedHeroProps {
  article: ArticleSummary;
}

export function FeaturedHero({ article }: FeaturedHeroProps) {
  const categoryName = article.category?.name || "Tiêu điểm";
  const categorySlug = article.category?.slug;
  const timeFormatted = formatDateVi(article.published_at);

  return (
    <div className="relative rounded-2xl overflow-hidden bg-gradient-to-t from-black/90 via-black/40 to-transparent text-white group shadow-xl">
      {/* Background Image */}
      {article.thumbnail_url ? (
        <div className="w-full h-[380px] sm:h-[460px] relative overflow-hidden">
          <img
            src={article.thumbnail_url}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/40 to-transparent" />
        </div>
      ) : (
        <div className="w-full h-[380px] bg-neutral-800" />
      )}

      {/* Content overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-5 sm:p-8 max-w-4xl">
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-brand-600 text-white shadow-sm">
            <Sparkles className="w-3 h-3" />
            {categoryName}
          </span>
          {timeFormatted && (
            <span className="text-xs text-neutral-300 inline-flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {timeFormatted}
            </span>
          )}
        </div>

        <Link href={`/article/${article.id}`}>
          <h2 className="text-xl sm:text-3xl font-extrabold text-white group-hover:text-brand-200 transition-colors leading-tight line-clamp-3 drop-shadow-md">
            {article.title}
          </h2>
        </Link>

        {article.description && (
          <p className="mt-3 text-sm sm:text-base text-neutral-200 line-clamp-2 leading-relaxed drop-shadow">
            {article.description}
          </p>
        )}

        <div className="flex items-center gap-4 mt-4 text-xs text-neutral-300">
          {article.author && (
            <span className="inline-flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-neutral-400" />
              {article.author}
            </span>
          )}
          <Link
            href={`/article/${article.id}`}
            className="inline-flex items-center font-semibold text-brand-300 hover:text-white transition-colors"
          >
            Đọc toàn bộ bài viết &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
