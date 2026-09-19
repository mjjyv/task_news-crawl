"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Clock, User, BookOpen, ExternalLink, ImageIcon, Flame, MessageSquare } from "lucide-react";
import { ArticleDetail } from "@/lib/types";
import { formatDateVi, estimateReadingTime, sanitizeContentHtml } from "@/lib/utils";
import { ReaderControls } from "./ReaderControls";
import { ArticleCard } from "./ArticleCard";

interface ArticleReaderViewProps {
  article: ArticleDetail;
}

export function ArticleReaderView({ article }: ArticleReaderViewProps) {
  const [fontSize, setFontSize] = useState<number>(18);
  const timeFormatted = formatDateVi(article.published_at);
  const readingTime = estimateReadingTime(article.content_text);
  const cleanHtml = sanitizeContentHtml(article.content_html);
  const commentCount = article.comment_count ?? 0;
  const isHot = commentCount >= 10;

  return (
    <article className="max-w-3xl mx-auto py-2 text-[#EAEAEA]">
      {/* Article Header */}
      <header className="space-y-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[10px]">
          {article.category && (
            <Link
              href={`/category/${article.category.slug}`}
              className="px-2 py-0.5 bg-[#E61919] text-white font-bold uppercase tracking-widest border border-[#E61919]"
            >
              [ {article.category.name} ]
            </Link>
          )}

          {/* Comment Count Telemetry Indicator */}
          {isHot ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-[#E61919] text-white font-bold uppercase tracking-wider border border-[#E61919] shadow-[0_0_8px_rgba(230,25,25,0.4)]">
              <Flame className="w-3 h-3 fill-white" />
              <span>HOT WIRE // {commentCount} BÌNH LUẬN</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#1A1A1A] text-[#EAEAEA] border border-[#333] tracking-wider">
              <MessageSquare className="w-3 h-3 text-[#8A8A8A]" />
              <span>COMMENTS // {String(commentCount).padStart(3, "0")}</span>
            </span>
          )}

          <span className="text-[#555] ml-auto">UNIT // {article.id}</span>
        </div>

        <h1 className="text-2xl sm:text-4xl font-extrabold text-[#EAEAEA] tracking-tight leading-tight font-sans">
          {article.title}
        </h1>

        {/* Tactical Telemetry HUD Bar */}
        <div className="flex flex-wrap items-center gap-4 py-2.5 border-y border-[#262626] font-mono text-xs text-[#8A8A8A]">
          {timeFormatted && (
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#666]" />
              <span>[ {timeFormatted} ]</span>
            </div>
          )}

          {article.author && (
            <div className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-[#666]" />
              <span className="text-[#CCC]">[ {article.author} ]</span>
            </div>
          )}

          <div className="flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-[#666]" />
            <span>[ {readingTime} ]</span>
          </div>

          <div className="flex items-center gap-1.5 text-[#E61919]">
            <span>[ {commentCount} COMMENTS ]</span>
          </div>
        </div>

        {/* Reader Customization Controls */}
        <ReaderControls
          articleId={article.id}
          originUrl={article.origin_url}
          fontSize={fontSize}
          onFontSizeChange={setFontSize}
        />

        {/* Description / Sapo */}
        {article.description && (
          <p className="text-base sm:text-lg font-bold text-[#D4D4D4] leading-relaxed font-sans border-l-2 border-[#E61919] pl-3 py-1">
            {article.description}
          </p>
        )}
      </header>

      {/* Main Body Content with dynamic font size */}
      <div
        className="article-reader-content font-serif leading-relaxed text-[#D4D4D4]"
        style={{ fontSize: `${fontSize}px` }}
        dangerouslySetInnerHTML={{ __html: cleanHtml }}
      />

      {/* Media Gallery (if more images attached) */}
      {article.media && article.media.length > 1 && (
        <section className="mt-10 pt-6 border-t border-[#262626]">
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#8A8A8A] mb-4 flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-[#E61919]" />
            THƯ VIỆN HÌNH ẢNH [ {article.media.length} ẢNH ]
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {article.media.map((m) => (
              <figure key={m.id} className="bg-[#121212] border border-[#262626] p-2">
                <img
                  src={m.url}
                  alt={m.caption || article.title}
                  className="w-full h-48 object-cover hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                {m.caption && (
                  <figcaption className="p-2 text-xs font-mono text-[#8A8A8A] italic">
                    {m.caption}
                  </figcaption>
                )}
              </figure>
            ))}
          </div>
        </section>
      )}

      {/* Original Source Footnote */}
      <div className="my-8 p-4 bg-[#121212] border border-[#262626] flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-xs text-[#8A8A8A]">
        <span>
          NGUỒN GỐC // NỘI DUNG THU THẬP TỪ BÁO ĐIỆN TỬ VNEXPRESS
        </span>
        <a
          href={article.origin_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 font-bold text-[#E61919] hover:underline shrink-0"
        >
          <span>[ BÀI VIẾT GỐC ]</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* Related Articles Section */}
      {article.related_articles && article.related_articles.length > 0 && (
        <section className="mt-12 pt-8 border-t border-[#262626]">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-[#262626]">
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#EAEAEA]">
              [ BÀI VIẾT LIÊN QUAN TRONG CÙNG CHUYÊN MỤC ]
            </h3>
            <span className="font-mono text-[10px] text-[#8A8A8A]">
              {article.related_articles.length} UNITS
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {article.related_articles.map((related) => (
              <ArticleCard key={related.id} article={related} variant="grid" />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
