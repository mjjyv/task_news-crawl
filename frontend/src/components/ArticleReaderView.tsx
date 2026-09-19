"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Clock, User, BookOpen, ExternalLink, ImageIcon } from "lucide-react";
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

  return (
    <article className="max-w-3xl mx-auto py-2">
      {/* Article Header */}
      <header className="space-y-4 mb-6">
        {article.category && (
          <Link
            href={`/category/${article.category.slug}`}
            className="inline-block text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 hover:underline"
          >
            {article.category.name}
          </Link>
        )}

        <h1 className="text-2xl sm:text-4xl font-extrabold text-neutral-900 dark:text-neutral-50 tracking-tight leading-tight">
          {article.title}
        </h1>

        {/* Metadata Bar */}
        <div className="flex flex-wrap items-center gap-4 py-3 border-y border-neutral-200 dark:border-neutral-800 text-xs text-neutral-500 dark:text-neutral-400">
          {timeFormatted && (
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-neutral-400" />
              <span>{timeFormatted}</span>
            </div>
          )}

          {article.author && (
            <div className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-neutral-400" />
              <span className="font-medium text-neutral-700 dark:text-neutral-300">{article.author}</span>
            </div>
          )}

          <div className="flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-neutral-400" />
            <span>{readingTime}</span>
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
          <p className="text-base sm:text-lg font-semibold text-neutral-700 dark:text-neutral-200 leading-relaxed font-serif">
            {article.description}
          </p>
        )}
      </header>

      {/* Main Body Content with dynamic font size */}
      <div
        className="article-reader-content text-neutral-800 dark:text-neutral-200 font-serif leading-relaxed"
        style={{ fontSize: `${fontSize}px` }}
        dangerouslySetInnerHTML={{ __html: cleanHtml }}
      />

      {/* Media Gallery (if more images attached) */}
      {article.media && article.media.length > 1 && (
        <section className="mt-10 pt-6 border-t border-neutral-200 dark:border-neutral-800">
          <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-4 flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-brand-600" />
            Thư viện hình ảnh ({article.media.length} ảnh)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {article.media.map((m) => (
              <figure key={m.id} className="rounded-xl overflow-hidden bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700/60">
                <img
                  src={m.url}
                  alt={m.caption || article.title}
                  className="w-full h-48 object-cover hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                {m.caption && (
                  <figcaption className="p-3 text-xs text-neutral-500 dark:text-neutral-400 italic">
                    {m.caption}
                  </figcaption>
                )}
              </figure>
            ))}
          </div>
        </section>
      )}

      {/* Original Source Footnote */}
      <div className="my-8 p-4 rounded-xl bg-neutral-100 dark:bg-neutral-800/60 border border-neutral-200 dark:border-neutral-700/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <span className="text-neutral-500">
          Nguồn nội dung gốc được thu thập từ báo điện tử VnExpress
        </span>
        <a
          href={article.origin_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 font-semibold text-brand-600 dark:text-brand-400 hover:underline shrink-0"
        >
          <span>Xem bài viết gốc</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* Related Articles Section */}
      {article.related_articles && article.related_articles.length > 0 && (
        <section className="mt-12 pt-8 border-t border-neutral-200 dark:border-neutral-800">
          <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 mb-6">
            Bài viết liên quan trong cùng chuyên mục
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {article.related_articles.map((related) => (
              <ArticleCard key={related.id} article={related} variant="grid" />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
