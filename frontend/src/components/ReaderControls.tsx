"use client";

import React, { useState } from "react";
import { Copy, Check, ExternalLink, ZoomIn, ZoomOut, RotateCcw, Share2 } from "lucide-react";

interface ReaderControlsProps {
  articleId: number;
  originUrl: string;
  fontSize: number; // in pixels, e.g. 18
  onFontSizeChange: (size: number) => void;
}

export function ReaderControls({
  articleId,
  originUrl,
  fontSize,
  onFontSizeChange,
}: ReaderControlsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 py-3 px-4 rounded-xl bg-neutral-100/80 dark:bg-neutral-800/80 border border-neutral-200 dark:border-neutral-700/60 my-6 text-xs text-neutral-700 dark:text-neutral-300">
      {/* Font Resizer */}
      <div className="flex items-center gap-1.5">
        <span className="font-medium mr-1 text-neutral-500 dark:text-neutral-400">Cỡ chữ:</span>
        <button
          onClick={() => onFontSizeChange(Math.max(14, fontSize - 2))}
          type="button"
          className="p-1.5 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
          title="Giảm cỡ chữ"
          aria-label="Giảm cỡ chữ"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <span className="font-semibold px-1 min-w-[28px] text-center">{fontSize}px</span>
        <button
          onClick={() => onFontSizeChange(Math.min(24, fontSize + 2))}
          type="button"
          className="p-1.5 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
          title="Tăng cỡ chữ"
          aria-label="Tăng cỡ chữ"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        {fontSize !== 18 && (
          <button
            onClick={() => onFontSizeChange(18)}
            type="button"
            className="p-1.5 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-400 hover:text-neutral-600 transition-colors"
            title="Đặt lại cỡ chữ mặc định (18px)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleCopy}
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800 font-medium transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-emerald-600 dark:text-emerald-400">Đã sao chép!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-neutral-500" />
              <span>Sao chép link</span>
            </>
          )}
        </button>

        <a
          href={originUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800 font-medium transition-colors"
          title="Xem bài viết gốc trên VnExpress"
        >
          <ExternalLink className="w-3.5 h-3.5 text-neutral-500" />
          <span>VnExpress gốc</span>
        </a>
      </div>
    </div>
  );
}
