import React from "react";
import Link from "next/link";
import { ShieldCheck, Activity, Github } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full bg-[#0A0A0A] border-t border-[#262626] text-[#8A8A8A] text-xs py-8 transition-colors mt-auto font-mono">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-6 border-b border-[#262626]">
          {/* Brand Col */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-[#E61919] text-white font-bold text-xs tracking-wider">
                VNE
              </span>
              <span className="font-bold text-sm text-[#EAEAEA]">
                TELEMETRY TERMINAL v2.0
              </span>
            </div>
            <p className="text-[11px] leading-relaxed text-[#777]">
              Trải nghiệm đọc báo trực tuyến tối giản, phi thương mại hóa, giải mã nội dung từ VnExpress. Bổ sung trích xuất và giám sát lưu lượng bình luận.
            </p>
          </div>

          {/* Quick Nav */}
          <div>
            <h4 className="font-bold text-[#EAEAEA] mb-2 text-xs uppercase tracking-wider">
              [ CHUYÊN MỤC CHÍNH ]
            </h4>
            <div className="grid grid-cols-2 gap-1 text-[11px]">
              <Link href="/category/thoi-su" className="hover:text-[#E61919] transition-colors">
                // Thời sự
              </Link>
              <Link href="/category/khoa-hoc-cong-nghe" className="hover:text-[#E61919] transition-colors">
                // Khoa học CN
              </Link>
              <Link href="/category/kinh-doanh" className="hover:text-[#E61919] transition-colors">
                // Kinh doanh
              </Link>
              <Link href="/category/giai-tri" className="hover:text-[#E61919] transition-colors">
                // Giải trí
              </Link>
            </div>
          </div>

          {/* System status */}
          <div className="space-y-2">
            <h4 className="font-bold text-[#EAEAEA] mb-2 text-xs uppercase tracking-wider">
              [ TRẠNG THÁI HỆ THỐNG ]
            </h4>
            <div className="space-y-1 text-[11px]">
              <Link
                href="/crawler"
                className="inline-flex items-center gap-1.5 text-[#8A8A8A] hover:text-[#E61919] transition-colors"
              >
                <Activity className="w-3.5 h-3.5 text-[#E61919]" />
                <span>Bảng điều khiển Crawler & Dữ liệu</span>
              </Link>
              <div className="flex items-center gap-1.5 text-[#666]">
                <ShieldCheck className="w-3.5 h-3.5 text-[#4AF626]" />
                <span>FastAPI Clean Arch + Next.js Telemetry</span>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] text-[#555]">
          <p>© 2026 VNEXPRESS TELEMETRY TERMINAL. RAW DATA PARSED FROM VNEXPRESS.NET</p>
          <p>INDUSTRIAL BRUTALISM & TACTICAL TELEMETRY INTERFACE</p>
        </div>
      </div>
    </footer>
  );
}
