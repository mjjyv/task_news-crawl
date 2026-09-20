import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { getCategories } from "@/lib/api";
import { CategoryTreeItem } from "@/lib/types";

export const metadata: Metadata = {
  title: "VnExpress News Reader | Nền tảng đọc báo tối giản",
  description:
    "Hệ thống thu thập và đọc tin tức tự động từ VnExpress, tối ưu hóa tốc độ, loại bỏ quảng cáo và bảo vệ quyền riêng tư.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let categories: CategoryTreeItem[] = [];
  try {
    categories = await getCategories(true);
  } catch (err) {
    // If backend is not running during initial static build, fallback gracefully
    console.warn("Failed to fetch initial categories for Header:", err);
  }

  return (
    <html lang="vi" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col bg-[#fafafa] dark:bg-[#0f0f0f] text-neutral-900 dark:text-neutral-100 antialiased selection:bg-brand-500 selection:text-white">
        <ThemeProvider>
          <Header categories={categories} />
          <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </main>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
