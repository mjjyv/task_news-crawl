"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Activity } from "lucide-react";
import { getCrawlerHealth } from "@/lib/api";

export function CrawlerHealthBadge() {
  const [status, setStatus] = useState<"healthy" | "degraded" | "offline">("healthy");
  const [articleCount, setArticleCount] = useState<number | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const data = await getCrawlerHealth();
        if (!isMounted) return;
        if (data.status === "healthy" && data.database_connected) {
          setStatus("healthy");
        } else {
          setStatus("degraded");
        }
        setArticleCount(data.total_articles);
      } catch {
        if (!isMounted) return;
        setStatus("offline");
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <Link
      href="/crawler"
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
      title={`Trạng thái hệ thống: ${status.toUpperCase()} ${articleCount !== null ? `(${articleCount} bài)` : ""}`}
    >
      <span className="relative flex h-2 w-2">
        {status === "healthy" && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        )}
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${
            status === "healthy"
              ? "bg-emerald-500"
              : status === "degraded"
              ? "bg-amber-500"
              : "bg-rose-500"
          }`}
        ></span>
      </span>
      <span className="hidden sm:inline">
        {status === "healthy" ? "Hệ thống Online" : status === "degraded" ? "Cảnh báo" : "Offline"}
      </span>
      {articleCount !== null && (
        <span className="hidden md:inline font-semibold text-neutral-500 dark:text-neutral-400">
          • {articleCount} bài
        </span>
      )}
      <Activity className="w-3 h-3 text-neutral-400" />
    </Link>
  );
}
