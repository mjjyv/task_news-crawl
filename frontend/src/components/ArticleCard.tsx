import React from "react";
import Link from "next/link";
import { Clock, User, Flame, MessageSquare } from "lucide-react";
import { ArticleSummary } from "@/lib/types";
import { formatDateVi } from "@/lib/utils";

interface ArticleCardProps {
  article: ArticleSummary;
  variant?: "grid" | "list" | "compact";
}

export function ArticleCard({ article, variant = "grid" }: ArticleCardProps) {
  const categoryName = article.category?.name || "TIN TỨC";
  const categorySlug = article.category?.slug;
  const timeFormatted = formatDateVi(article.published_at);
  const commentCount = article.comment_count ?? 0;
  const isHot = commentCount >= 10;

  // Telemetry comment badge
  const renderCommentBadge = (size: "sm" | "md" = "md") => {
    if (isHot) {
      return (
        <span
          className={`inline-flex items-center gap-1 font-mono font-bold uppercase tracking-wider bg-[#E61919] text-white border border-[#E61919] shadow-[0_0_8px_rgba(230,25,25,0.4)] ${
            size === "sm" ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-[10px]"
          }`}
          title={`Bài viết HOT: ${commentCount} lượt bình luận`}
        >
          <Flame className={size === "sm" ? "w-2.5 h-2.5 fill-white" : "w-3 h-3 fill-white"} />
          <span>HOT // {commentCount} CMT</span>
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono uppercase tracking-wider bg-[#1A1A1A] text-[#EAEAEA] border border-[#333333] ${
          size === "sm" ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-[10px]"
        }`}
        title={`${commentCount} bình luận`}
      >
        <MessageSquare className={size === "sm" ? "w-2.5 h-2.5 text-[#8A8A8A]" : "w-3 h-3 text-[#8A8A8A]"} />
        <span>CMT // {String(commentCount).padStart(3, "0")}</span>
      </span>
    );
  };

  if (variant === "compact") {
    return (
      <article className="group flex items-start gap-3 py-3 border-b border-[#262626] last:border-0 hover:bg-[#141414] px-2 transition-colors">
        {article.thumbnail_url && (
          <Link
            href={`/article/${article.id}`}
            className="w-16 h-16 shrink-0 overflow-hidden bg-[#1A1A1A] border border-[#262626] relative block"
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
          <div className="flex items-center gap-2 mb-1">
            {renderCommentBadge("sm")}
          </div>
          <Link href={`/article/${article.id}`}>
            <h4 className="text-xs font-bold text-[#EAEAEA] group-hover:text-[#E61919] line-clamp-2 transition-colors font-sans">
              {article.title}
            </h4>
          </Link>
          <div className="flex items-center gap-2 mt-1.5 font-mono text-[10px] text-[#8A8A8A]">
            {timeFormatted && <span>// {timeFormatted}</span>}
          </div>
        </div>
      </article>
    );
  }

  if (variant === "list") {
    return (
      <article className="group flex flex-col sm:flex-row gap-4 p-4 bg-[#121212] border border-[#262626] hover:border-[#E61919] transition-all relative">
        {article.thumbnail_url && (
          <Link
            href={`/article/${article.id}`}
            className="sm:w-56 h-36 shrink-0 overflow-hidden bg-[#1A1A1A] border border-[#262626] relative block"
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
            <div className="flex flex-wrap items-center gap-2 mb-2">
              {categorySlug ? (
                <Link
                  href={`/category/${categorySlug}`}
                  className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#8A8A8A] hover:text-[#E61919] border border-[#262626] px-1.5 py-0.5 bg-[#0A0A0A]"
                >
                  [ {categoryName} ]
                </Link>
              ) : (
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#8A8A8A] border border-[#262626] px-1.5 py-0.5 bg-[#0A0A0A]">
                  [ {categoryName} ]
                </span>
              )}

              {/* Comment Count Telemetry Badge */}
              {renderCommentBadge("md")}

              <span className="font-mono text-[9px] text-[#555] ml-auto">
                ID // {article.id}
              </span>
            </div>

            <Link href={`/article/${article.id}`}>
              <h3 className="text-base sm:text-lg font-extrabold text-[#EAEAEA] group-hover:text-[#E61919] line-clamp-2 transition-colors font-sans tracking-tight">
                {article.title}
              </h3>
            </Link>

            {article.description && (
              <p className="mt-2 text-xs sm:text-sm text-[#A0A0A0] line-clamp-2 leading-relaxed">
                {article.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3 mt-3 pt-2.5 border-t border-[#1F1F1F] font-mono text-[10px] text-[#8A8A8A]">
            {timeFormatted && (
              <span className="inline-flex items-center gap-1">
                <Clock className="w-3 h-3 text-[#666]" />
                {timeFormatted}
              </span>
            )}
            {article.author && (
              <span className="inline-flex items-center gap-1">
                <User className="w-3 h-3 text-[#666]" />
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
    <article className="group flex flex-col bg-[#121212] border border-[#262626] hover:border-[#E61919] transition-all relative">
      {article.thumbnail_url ? (
        <Link
          href={`/article/${article.id}`}
          className="w-full aspect-[16/10] overflow-hidden bg-[#1A1A1A] border-b border-[#262626] relative block"
        >
          <img
            src={article.thumbnail_url}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
          {/* Top-Right corner badge on thumbnail */}
          <div className="absolute top-2 right-2">
            {renderCommentBadge("sm")}
          </div>
        </Link>
      ) : (
        <div className="w-full aspect-[16/10] bg-[#171717] border-b border-[#262626] flex items-center justify-center text-[#555] font-mono text-[10px] uppercase">
          NO VISUAL TELEMETRY
        </div>
      )}

      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between gap-2 mb-2.5">
            {categorySlug ? (
              <Link
                href={`/category/${categorySlug}`}
                className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#8A8A8A] hover:text-[#E61919] border border-[#262626] px-1.5 py-0.5 bg-[#0A0A0A]"
              >
                [ {categoryName} ]
              </Link>
            ) : (
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#8A8A8A] border border-[#262626] px-1.5 py-0.5 bg-[#0A0A0A]">
                [ {categoryName} ]
              </span>
            )}

            {!article.thumbnail_url && renderCommentBadge("sm")}
            <span className="font-mono text-[9px] text-[#555]">
              #{article.id}
            </span>
          </div>

          <Link href={`/article/${article.id}`}>
            <h3 className="text-base font-extrabold text-[#EAEAEA] group-hover:text-[#E61919] line-clamp-2 transition-colors font-sans tracking-tight">
              {article.title}
            </h3>
          </Link>

          {article.description && (
            <p className="mt-2 text-xs text-[#A0A0A0] line-clamp-3 leading-relaxed">
              {article.description}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between gap-2 mt-4 pt-3 border-t border-[#1F1F1F] font-mono text-[10px] text-[#8A8A8A]">
          {timeFormatted && (
            <span className="inline-flex items-center gap-1">
              <Clock className="w-3 h-3 text-[#666]" />
              {timeFormatted}
            </span>
          )}
          {article.author && (
            <span className="inline-flex items-center gap-1 truncate max-w-[120px]">
              <User className="w-3 h-3 text-[#666]" />
              {article.author}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}
