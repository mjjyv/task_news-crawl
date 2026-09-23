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
    proxy_url = getattr(args, "proxy", None)
    pipeline = ArticlePipeline(proxy_url=proxy_url)
    result = pipeline.crawl_category(
        category_slug=args.slug,
        max_pages=args.pages,
        max_articles=args.max_articles,
        recursive=getattr(args, "recursive", False),
    )
    rec_str = " (kèm toàn bộ danh mục con)" if getattr(args, "recursive", False) else ""
    print(
        f"\nCrawl category '{args.slug}'{rec_str} hoàn tất: "
        f"Tìm thấy {result['articles_found']} bài viết, thu thập mới {result['articles_new']} bài."
    )


def cmd_crawl_rss(args):
    init_db()
    proxy_url = getattr(args, "proxy", None)
    pipeline = ArticlePipeline(proxy_url=proxy_url)
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
    proxy_url = getattr(args, "proxy", None)
    pipeline = ArticlePipeline(proxy_url=proxy_url)
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


def cmd_update_comments(args):
    init_db()
    from crawler.storage.models import Article
    from sqlalchemy import select
    import concurrent.futures

    proxy_url = getattr(args, "proxy", None)
    pipeline = ArticlePipeline(proxy_url=proxy_url)
    with get_db_session() as session:
        stmt = select(Article.id, Article.title, Article.comment_count).order_by(Article.published_at.desc().nulls_last())
        if args.limit and args.limit > 0:
            stmt = stmt.limit(args.limit)
        rows = session.execute(stmt).all()
        article_items = [(r[0], r[1], r[2]) for r in rows]

    total_articles = len(article_items)
    print(f"\n--- ĐỒNG BỘ LƯỢT BÌNH LUẬN TRỰC TIẾP TỪ VNEXPRESS ({total_articles} bài viết) ---")

    def fetch_one(item):
        aid, title, old_c = item
        live_c = pipeline.fetch_live_comment_count(aid)
        return aid, title, old_c, live_c

    results = []
    updated_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for idx, (aid, title, old_c, live_c) in enumerate(executor.map(fetch_one, article_items), 1):
            results.append((aid, live_c))
            if live_c > 0 and live_c != old_c:
                updated_count += 1
                print(f"  [{idx}/{total_articles}] [+] Bài {aid}: {old_c} -> {live_c} bình luận ({title[:42]}...)")
            elif idx % 25 == 0 or idx == total_articles:
                print(f"  [{idx}/{total_articles}] Đang xử lý... ({updated_count} bài có bình luận mới)")

    # Batch update into DB
    with get_db_session() as session:
        for aid, live_c in results:
            if live_c > 0:
                art = session.get(Article, aid)
                if art:
                    art.comment_count = live_c

    print(f"\nHoàn tất! Đã cập nhật số lượng bình luận mới cho {updated_count}/{total_articles} bài viết.\n")


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
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("-v", "--verbose", action="store_true", help="Bật log chi tiết (DEBUG)")
    common_parser.add_argument(
        "--proxy",
        "-p",
        default=None,
        help="Địa chỉ Proxy (HTTP/HTTPS hoặc SOCKS5, vd: socks5://127.0.0.1:40000, http://user:pass@ip:port)",
    )

    parser = argparse.ArgumentParser(
        description="VnExpress News Aggregator - Crawler Core CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[common_parser],
    )
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực thi")

    # init-db
    p_init = subparsers.add_parser("init-db", parents=[common_parser], help="Khởi tạo cấu trúc bảng Database")
    p_init.set_defaults(func=cmd_init_db)

    # sync-categories
    p_sync = subparsers.add_parser("sync-categories", parents=[common_parser], help="Đồng bộ toàn bộ danh mục cha và con từ VnExpress")
    p_sync.set_defaults(func=cmd_sync_categories)

    # list-categories
    p_list_cat = subparsers.add_parser("list-categories", parents=[common_parser], help="Xem cây danh mục hiện có")
    p_list_cat.set_defaults(func=cmd_list_categories)

    # crawl-category
    p_cat = subparsers.add_parser("crawl-category", parents=[common_parser], help="Crawl bài viết từ một chuyên mục")
    p_cat.add_argument("slug", help="Slug chuyên mục (vd: khoa-hoc-cong-nghe, thoi-su, the-gioi)")
    p_cat.add_argument("--pages", type=int, default=1, help="Số lượng trang cần duyệt (1 đến 20)")
    p_cat.add_argument("--max-articles", type=int, default=None, help="Giới hạn tối đa số bài viết mới")
    p_cat.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Tự động duyệt đệ quy toàn bộ các chuyên mục con thuộc chuyên mục này",
    )
    p_cat.set_defaults(func=cmd_crawl_category)

    # crawl-rss
    p_rss = subparsers.add_parser("crawl-rss", parents=[common_parser], help="Cập nhật tin mới nhất qua RSS feed")
    p_rss.add_argument("--topic", default="tin-moi-nhat", help="Topic RSS (vd: tin-moi-nhat, khoa-hoc-cong-nghe, thoi-su)")
    p_rss.add_argument("--max-articles", type=int, default=None, help="Giới hạn số bài viết mới")
    p_rss.set_defaults(func=cmd_crawl_rss)

    # crawl-article
    p_art = subparsers.add_parser("crawl-article", parents=[common_parser], help="Crawl chi tiết một bài viết cụ thể qua URL")
    p_art.add_argument("url", help="URL bài viết VnExpress (*-<id>.html)")
    p_art.set_defaults(func=cmd_crawl_article)

    # update-comments
    p_ucmt = subparsers.add_parser("update-comments", parents=[common_parser], help="Đồng bộ số lượng bình luận thời gian thực từ VnExpress")
    p_ucmt.add_argument("--limit", type=int, default=50, help="Số lượng bài viết tối đa cần đồng bộ (mặc định 50)")
    p_ucmt.set_defaults(func=cmd_update_comments)

    # stats
    p_stats = subparsers.add_parser("stats", parents=[common_parser], help="Xem thống kê tổng quan dữ liệu đã thu thập")
    p_stats.set_defaults(func=cmd_stats)

    # cron-run
    p_cron = subparsers.add_parser("cron-run", parents=[common_parser], help="Thực thi hoặc xem lịch trình Cronjob phân bổ hằng tuần")
    p_cron.add_argument(
        "--mode",
        choices=["hourly", "daily", "all", "maintenance", "schedule"],
        default="daily",
        help="Chế độ chạy: hourly, daily, all, maintenance, schedule",
    )
    p_cron.add_argument(
        "--day",
        choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun", "today"],
        default="today",
        help="Thứ trong tuần (dùng cho daily)",
    )
    p_cron.add_argument(
        "--slot",
        choices=["slot1", "slot2", "slot3"],
        default=None,
        help="Khung giờ trong ngày (slot1, slot2, slot3)",
    )
    p_cron.add_argument("--max-articles", type=int, default=100, help="Số bài viết mới tối đa / mục")
    p_cron.add_argument("--pages", type=int, default=7, help="Số trang danh mục tối đa cần duyệt")
    p_cron.set_defaults(func=lambda a: __import__("crawler.cron", fromlist=["main"]).main_cli(a))

    args = parser.parse_args()
    setup_logging(args.verbose)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
