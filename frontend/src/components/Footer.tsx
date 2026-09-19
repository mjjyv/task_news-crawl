import React from "react";
import Link from "next/link";
import { ShieldCheck, Activity, Github } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full bg-neutral-100 dark:bg-neutral-950 border-t border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400 text-xs py-10 transition-colors mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-8 border-b border-neutral-200 dark:border-neutral-800/80">
          {/* Brand Col */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-brand-600 text-white font-bold flex items-center justify-center text-xs">
                V
              </span>
              <span className="font-bold text-sm text-neutral-900 dark:text-neutral-100">
                VnExpress Reader
              </span>
            </div>
            <p className="leading-relaxed">
              Trải nghiệm đọc báo trực tuyến tối giản, tải trang tức thì, bảo vệ quyền riêng tư và hoàn toàn không quảng cáo phiền toái.
            </p>
          </div>

          {/* Quick Nav */}
          <div>
            <h4 className="font-semibold text-neutral-900 dark:text-neutral-200 mb-3 text-xs uppercase tracking-wider">
              Chuyên mục tiêu điểm
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <Link href="/category/thoi-su" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
                Thời sự
              </Link>
              <Link href="/category/khoa-hoc-cong-nghe" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
                Khoa học công nghệ
              </Link>
              <Link href="/category/kinh-doanh" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
                Kinh doanh
              </Link>
              <Link href="/category/giai-tri" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
                Giải trí
              </Link>
            </div>
          </div>

          {/* System status */}
          <div className="space-y-2">
            <h4 className="font-semibold text-neutral-900 dark:text-neutral-200 mb-3 text-xs uppercase tracking-wider">
              Hệ thống
            </h4>
            <div className="space-y-1.5">
              <Link
                href="/crawler"
                className="inline-flex items-center gap-2 text-neutral-600 dark:text-neutral-400 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
              >
                <Activity className="w-3.5 h-3.5 text-brand-600" />
                <span>Bảng điều khiển Crawler & Dữ liệu</span>
              </Link>
              <div className="flex items-center gap-2 text-neutral-500">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span>Clean Architecture • FastAPI + Next.js</span>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-neutral-500">
          <p>© 2026 VnExpress News Aggregator. Dữ liệu tổng hợp từ Báo điện tử VnExpress.</p>
          <p>Thiết kế hướng tới trải nghiệm người đọc tối giản.</p>
        </div>
      </div>
    </footer>
  );
}
