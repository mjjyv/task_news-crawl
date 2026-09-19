import React from "react";
import Link from "next/link";
import { Clock, User, Flame, MessageSquare, ArrowRight } from "lucide-react";
import { ArticleSummary } from "@/lib/types";
import { formatDateVi } from "@/lib/utils";

interface FeaturedHeroProps {
  article: ArticleSummary;
}

export function FeaturedHero({ article }: FeaturedHeroProps) {
  const categoryName = article.category?.name || "TIÊU ĐIỂM";
  const categorySlug = article.category?.slug;
  const timeFormatted = formatDateVi(article.published_at);
  const commentCount = article.comment_count ?? 0;
  const isHot = commentCount >= 10;

  return (
    <div className="relative bg-[#121212] border border-[#262626] text-[#EAEAEA] group overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-12">
        {/* Left: Thumbnail container */}
        <div className="lg:col-span-7 relative h-72 sm:h-96 lg:h-auto overflow-hidden bg-[#1A1A1A] border-b lg:border-b-0 lg:border-r border-[#262626]">
          {article.thumbnail_url ? (
            <img
              src={article.thumbnail_url}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center font-mono text-xs text-[#555]">
              [ NO PRIMARY FEED ]
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-[#121212] via-transparent to-transparent lg:hidden" />
        </div>

        {/* Right: Content details */}
        <div className="lg:col-span-5 p-6 sm:p-8 flex flex-col justify-between">
          <div>
            {/* Top Telemetry Row */}
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <span className="px-2 py-0.5 bg-[#E61919] text-white font-mono font-bold text-[10px] tracking-widest uppercase">
                [ LEAD STORY ]
              </span>

              {categorySlug ? (
                <Link
                  href={`/category/${categorySlug}`}
                  className="px-2 py-0.5 bg-[#1A1A1A] text-[#8A8A8A] hover:text-[#E61919] border border-[#333] font-mono text-[10px] uppercase tracking-wider"
                >
                  // {categoryName}
                </Link>
              ) : (
                <span className="px-2 py-0.5 bg-[#1A1A1A] text-[#8A8A8A] border border-[#333] font-mono text-[10px] uppercase tracking-wider">
                  // {categoryName}
                </span>
              )}

              {/* Comment Count Badge */}
              {isHot ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#E61919] text-white font-mono font-bold text-[10px] tracking-wider border border-[#E61919] shadow-[0_0_8px_rgba(230,25,25,0.4)]">
                  <Flame className="w-3 h-3 fill-white" />
                  <span>HOT // {commentCount} CMT</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#1A1A1A] text-[#EAEAEA] border border-[#333] font-mono text-[10px] tracking-wider">
                  <MessageSquare className="w-3 h-3 text-[#8A8A8A]" />
                  <span>CMT // {String(commentCount).padStart(3, "0")}</span>
                </span>
              )}
            </div>

            <Link href={`/article/${article.id}`}>
              <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-[#EAEAEA] group-hover:text-[#E61919] transition-colors leading-tight font-sans tracking-tight mb-3">
                {article.title}
              </h2>
            </Link>

            {article.description && (
              <p className="text-xs sm:text-sm text-[#A0A0A0] leading-relaxed line-clamp-3">
                {article.description}
              </p>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-[#262626] flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-[#8A8A8A]">
            <div className="flex items-center gap-3">
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

            <Link
              href={`/article/${article.id}`}
              className="inline-flex items-center gap-1 font-bold text-[#E61919] hover:underline"
            >
              <span>[ READ DISPATCH ]</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
