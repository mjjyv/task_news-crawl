"""Command-Line Interface (CLI) for VnExpress News Crawler."""

import argparse
import json
import logging
import sys
from typing import Optional

from crawler.config import settings
from crawler.deduplicator import get_deduplicator
from crawler.pipeline.article_pipeline import ArticlePipeline
from crawler.pipeline.category_sync import CategorySyncPipeline
from crawler.storage.database import get_db_session, init_db
from crawler.storage.repository import Repository


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_init_db(args):
    init_db()
    print("Database initialized successfully.")


def cmd_sync_categories(args):
    init_db()
    pipeline = CategorySyncPipeline()
    result = pipeline.sync_all()
    print(f"Categories synchronized: {result['parent_categories']} parent, {result['sub_categories']} subcategories.")


def cmd_list_categories(args):
    init_db()
    with get_db_session() as session:
        repo = Repository(session)
        categories = repo.get_all_categories()
        print(f"\n--- DANH MỤC HIỆN CÓ TRONG HỆ THỐNG ({len(categories)}) ---")
        parents = [c for c in categories if c.parent_id is None]
        for p in parents:
            print(f"📁 {p.name} (/{p.slug})")
            children = [c for c in categories if c.parent_id == p.id]
            for ch in children:
                print(f"   └── 📄 {ch.name} (/{ch.slug})")


def cmd_crawl_category(args):
    init_db()
    pipeline = ArticlePipeline()
    result = pipeline.crawl_category(
        category_slug=args.slug,
        max_pages=args.pages,
        max_articles=args.max_articles,
    )
    print(
        f"\nCrawl category '{args.slug}' hoàn tất: "
        f"Tìm thấy {result['articles_found']} bài viết, thu thập mới {result['articles_new']} bài."
    )


def cmd_crawl_rss(args):
    init_db()
    pipeline = ArticlePipeline()
    result = pipeline.crawl_rss(
        topic=args.topic,
        max_articles=args.max_articles,
    )
    print(
        f"\nCrawl RSS topic '{args.topic}' hoàn tất: "
        f"Tìm thấy {result['articles_found']} bài viết, thu thập mới {result['articles_new']} bài."
    )


def cmd_crawl_article(args):
    init_db()
    pipeline = ArticlePipeline()
    parsed = pipeline.crawl_single_article(args.url)
    if parsed:
        print("\n--- THU THẬP BÀI VIẾT THÀNH CÔNG ---")
        print(f"ID:           {parsed.id}")
        print(f"Tiêu đề:      {parsed.title}")
        print(f"Tác giả:      {parsed.author}")
        print(f"Ngày xuất bản:{parsed.published_at}")
        print(f"Chuyên mục:   {parsed.category_slug}")
        print(f"Số lượng ảnh: {len(parsed.media)}")
        print(f"Độ dài text:  {len(parsed.content_text)} ký tự")
        print(f"URL:          {parsed.origin_url}")
    else:
        print(f"Không thể thu thập bài viết từ URL: {args.url}")
        sys.exit(1)


def cmd_stats(args):
    init_db()
    with get_db_session() as session:
        repo = Repository(session)
        stats = repo.get_stats()
        dedup = get_deduplicator()
        seen_count = dedup.count()

        print("\n================ THỐNG KÊ CRAWLER CORE ================")
        print(f" Tổng số danh mục:      {stats['total_categories']}")
        print(f" Tổng số bài viết:      {stats['total_articles']}")
        print(f" Tổng số file media:    {stats['total_media']}")
        print(f" Số ID đã lưu lọc trùng:{seen_count}")
        print("\n Nhật ký cào dữ liệu gần nhất (Crawl Logs):")
        for log in stats["latest_logs"]:
            status_icon = "✅" if log["status"] == "success" else "❌"
            print(
                f"  {status_icon} [{log['type']}] target={log['target'][:40]}... "
                f"found={log['found']} new={log['new']} ({log['time']})"
            )
        print("========================================================\n")


def main():
    parser = argparse.ArgumentParser(
        description="VnExpress News Aggregator - Crawler Core CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Bật log chi tiết (DEBUG)")
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực thi")

    # init-db
    p_init = subparsers.add_parser("init-db", help="Khởi tạo cấu trúc bảng Database")
    p_init.set_defaults(func=cmd_init_db)

    # sync-categories
    p_sync = subparsers.add_parser("sync-categories", help="Đồng bộ toàn bộ danh mục cha và con từ VnExpress")
    p_sync.set_defaults(func=cmd_sync_categories)

    # list-categories
    p_list_cat = subparsers.add_parser("list-categories", help="Xem cây danh mục hiện có")
    p_list_cat.set_defaults(func=cmd_list_categories)

    # crawl-category
    p_cat = subparsers.add_parser("crawl-category", help="Crawl bài viết từ một chuyên mục")
    p_cat.add_argument("slug", help="Slug chuyên mục (vd: khoa-hoc-cong-nghe, thoi-su, the-gioi)")
    p_cat.add_argument("--pages", type=int, default=1, help="Số lượng trang cần duyệt (1 đến 20)")
    p_cat.add_argument("--max-articles", type=int, default=None, help="Giới hạn tối đa số bài viết mới")
    p_cat.set_defaults(func=cmd_crawl_category)

    # crawl-rss
    p_rss = subparsers.add_parser("crawl-rss", help="Cập nhật tin mới nhất qua RSS feed")
    p_rss.add_argument("--topic", default="tin-moi-nhat", help="Topic RSS (vd: tin-moi-nhat, khoa-hoc-cong-nghe, thoi-su)")
    p_rss.add_argument("--max-articles", type=int, default=None, help="Giới hạn số bài viết mới")
    p_rss.set_defaults(func=cmd_crawl_rss)

    # crawl-article
    p_art = subparsers.add_parser("crawl-article", help="Crawl chi tiết một bài viết cụ thể qua URL")
    p_art.add_argument("url", help="URL bài viết VnExpress (*-<id>.html)")
    p_art.set_defaults(func=cmd_crawl_article)

    # stats
    p_stats = subparsers.add_parser("stats", help="Xem thống kê tổng quan dữ liệu đã thu thập")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    setup_logging(args.verbose)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
