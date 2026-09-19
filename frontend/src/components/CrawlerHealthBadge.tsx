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
      className="inline-flex items-center gap-2 px-2.5 py-1.5 bg-[#121212] border border-[#262626] hover:border-[#4AF626] font-mono text-[11px] text-[#EAEAEA] transition-colors"
      title={`Trạng thái hệ thống: ${status.toUpperCase()} ${articleCount !== null ? `(${articleCount} bài)` : ""}`}
    >
      <span className="relative flex h-2 w-2">
        {status === "healthy" && (
          <span className="animate-ping absolute inline-flex h-full w-full bg-[#4AF626] opacity-75"></span>
        )}
        <span
          className={`relative inline-flex h-2 w-2 ${
            status === "healthy"
              ? "bg-[#4AF626]"
              : status === "degraded"
              ? "bg-[#F59E0B]"
              : "bg-[#E61919]"
          }`}
        ></span>
      </span>
      <span className="hidden sm:inline font-mono tracking-wider">
        {status === "healthy" ? "SYS // ONLINE" : status === "degraded" ? "SYS // WARN" : "SYS // OFFLINE"}
      </span>
      {articleCount !== null && (
        <span className="font-mono text-[#8A8A8A] hidden md:inline">
          [{articleCount.toString().padStart(2, "0")} ARTS]
        </span>
      )}
      <Activity className="w-3 h-3 text-[#8A8A8A]" />
    </Link>
  );
}
