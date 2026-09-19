"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  Database,
  Server,
  Layers,
  FileText,
  Play,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Sparkles,
} from "lucide-react";
import { getCrawlerHealth, triggerCrawl } from "@/lib/api";
import { CrawlerHealthResponse, CrawlLogItem } from "@/lib/types";
import { formatDateVi } from "@/lib/utils";

export default function CrawlerPage() {
  const [health, setHealth] = useState<CrawlerHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Trigger form state
  const [crawlType, setCrawlType] = useState<"rss" | "category">("rss");
  const [target, setTarget] = useState("tin-moi-nhat");
  const [maxArticles, setMaxArticles] = useState(10);
  const [pages, setPages] = useState(1);
  const [triggering, setTriggering] = useState(false);
  const [triggerMessage, setTriggerMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const fetchHealth = async () => {
    try {
      const data = await getCrawlerHealth();
      setHealth(data);
    } catch (err) {
      console.error("Failed to fetch crawler health:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealth();
  };

  const handleTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    setTriggering(true);
    setTriggerMessage(null);

    try {
      const res = await triggerCrawl({
        type: crawlType,
        target,
        max_articles: crawlType === "rss" ? maxArticles : undefined,
        pages: crawlType === "category" ? pages : undefined,
      });

      setTriggerMessage({
        type: "success",
        text: `Đã kích hoạt tác vụ cào tin ngầm: ${res.message} (Target: ${res.target})`,
      });

      // Re-fetch health after 3 seconds
      setTimeout(fetchHealth, 3000);
    } catch (err: any) {
      setTriggerMessage({
        type: "error",
        text: err.message || "Không thể kích hoạt tác vụ cào tin.",
      });
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-neutral-200 dark:border-neutral-800">
        <div>
          <div className="flex items-center gap-2 text-brand-600 dark:text-brand-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Activity className="w-4 h-4" />
            <span>Dashboard Quản trị</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-neutral-900 dark:text-neutral-100">
            Giám sát Crawler & Dữ liệu
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Theo dõi tình trạng kết nối backend, cơ sở dữ liệu và kích hoạt tác vụ cào tin tự động
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-200 text-xs font-semibold transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          <span>Làm mới trạng thái</span>
        </button>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: System Health */}
        <div className="p-5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
          <div className="flex items-center justify-between text-neutral-500 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Hệ thống</span>
            <Server className="w-4 h-4 text-brand-600" />
          </div>
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
              {health?.status === "healthy" ? "Hoạt động tốt" : "Đang kiểm tra"}
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-2">FastAPI Core v1.0.0</p>
        </div>

        {/* Card 2: Database */}
        <div className="p-5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
          <div className="flex items-center justify-between text-neutral-500 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Cơ sở dữ liệu</span>
            <Database className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
            {health?.database_connected ? "SQLite Connected" : "Chưa kết nối"}
          </div>
          <p className="text-xs text-neutral-400 mt-2">
            {health?.total_articles ?? 0} bài viết • {health?.total_categories ?? 0} chuyên mục
          </p>
        </div>

        {/* Card 3: Deduplicator */}
        <div className="p-5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
          <div className="flex items-center justify-between text-neutral-500 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Khử trùng lặp</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
            {health?.deduplicator_type || "In-Memory Set"}
          </div>
          <p className="text-xs text-neutral-400 mt-2">
            Đã lưu {health?.seen_ids_count ?? 0} ID bài viết
          </p>
        </div>

        {/* Card 4: Media Assets */}
        <div className="p-5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
          <div className="flex items-center justify-between text-neutral-500 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Tài nguyên Media</span>
            <FileText className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
            {health?.total_media ?? 0} tệp
          </div>
          <p className="text-xs text-neutral-400 mt-2">Hình ảnh & video bài viết</p>
        </div>
      </div>

      {/* Trigger Crawl Form */}
      <div className="p-6 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Play className="w-4 h-4 text-brand-600" />
          <h2 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
            Kích hoạt tác vụ cào tin tức thủ công (Background Tasks)
          </h2>
        </div>

        {triggerMessage && (
          <div
            className={`p-4 rounded-xl mb-5 flex items-start gap-3 text-xs ${
              triggerMessage.type === "success"
                ? "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800"
                : "bg-rose-50 dark:bg-rose-950/50 text-rose-800 dark:text-rose-200 border border-rose-200 dark:border-rose-800"
            }`}
          >
            {triggerMessage.type === "success" ? (
              <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            )}
            <span>{triggerMessage.text}</span>
          </div>
        )}

        <form onSubmit={handleTrigger} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Crawl Type Radio */}
            <div>
              <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
                Loại tác vụ cào
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setCrawlType("rss");
                    setTarget("tin-moi-nhat");
                  }}
                  className={`p-2.5 rounded-xl text-xs font-medium border text-center transition-all ${
                    crawlType === "rss"
                      ? "bg-brand-50 dark:bg-brand-950 border-brand-500 text-brand-700 dark:text-brand-300 font-bold"
                      : "border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400"
                  }`}
                >
                  RSS Feed (Tin mới)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setCrawlType("category");
                    setTarget("khoa-hoc-cong-nghe");
                  }}
                  className={`p-2.5 rounded-xl text-xs font-medium border text-center transition-all ${
                    crawlType === "category"
                      ? "bg-brand-50 dark:bg-brand-950 border-brand-500 text-brand-700 dark:text-brand-300 font-bold"
                      : "border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400"
                  }`}
                >
                  Chuyên mục (Listing)
                </button>
              </div>
            </div>

            {/* Target input */}
            <div>
              <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
                {crawlType === "rss" ? "Chủ đề RSS" : "Slug chuyên mục"}
              </label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder={crawlType === "rss" ? "tin-moi-nhat, tin-noi-bat..." : "khoa-hoc-cong-nghe, thoi-su..."}
                className="w-full px-3.5 py-2.5 rounded-xl bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {crawlType === "rss" ? (
              <div>
                <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
                  Số bài tối đa (1 - 50)
                </label>
                <input
                  type="number"
                  value={maxArticles}
                  min={1}
                  max={50}
                  onChange={(e) => setMaxArticles(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
                  Số trang cần duyệt (1 - 20)
                </label>
                <input
                  type="number"
                  value={pages}
                  min={1}
                  max={20}
                  onChange={(e) => setPages(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            )}

            <div className="flex items-end">
              <button
                type="submit"
                disabled={triggering}
                className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-2 shadow-sm"
              >
                {triggering ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                <span>Kích hoạt cào ngay (Async 202)</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Crawl Logs Table */}
      <div className="p-6 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm">
        <h2 className="text-base font-bold text-neutral-900 dark:text-neutral-100 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-600" />
          Nhật ký cào tin gần đây
        </h2>

        {health?.latest_logs && health.latest_logs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-400 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-3">Thời gian</th>
                  <th className="py-3 px-3">Loại</th>
                  <th className="py-3 px-3">Đích cào</th>
                  <th className="py-3 px-3">Trạng thái</th>
                  <th className="py-3 px-3">Tìm thấy</th>
                  <th className="py-3 px-3">Mới lưu</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800 text-neutral-700 dark:text-neutral-300">
                {health.latest_logs.map((log) => (
                  <tr key={log.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                    <td className="py-3 px-3 text-neutral-400 whitespace-nowrap">
                      {formatDateVi(log.executed_at)}
                    </td>
                    <td className="py-3 px-3 font-semibold uppercase text-[11px] text-brand-600 dark:text-brand-400">
                      {log.crawler_type}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] max-w-[200px] truncate" title={log.target_url}>
                      {log.target_url}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          log.status === "success"
                            ? "bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400"
                            : "bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-semibold">{log.articles_found}</td>
                    <td className="py-3 px-3 font-semibold text-emerald-600 dark:text-emerald-400">
                      +{log.articles_new}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-neutral-400 py-6 text-center">
            Chưa có nhật ký cào tin nào được ghi nhận.
          </p>
        )}
      </div>
    </div>
  );
}
