"""Cronjob Scheduler & Batch Runner for VnExpress News Crawler.

Handles:
1. Hourly 100 latest breaking news (via RSS feeds).
2. Daily category crawling distributed across 7 days and multiple time slots per day.
3. Sunday maintenance (live comments sync & SQLite VACUUM).
"""

import argparse
import datetime
import logging
import sys
import time
from typing import Any, Dict, List, Optional

from crawler.config import settings
from crawler.pipeline.article_pipeline import ArticlePipeline
from crawler.storage.database import get_db_session, init_db
from crawler.storage.models import Article, Category
from crawler.storage.repository import Repository

logger = logging.getLogger("crawler.cron")

# Bảng phân bổ 122 danh mục (17 cha + 105 con) theo tuần và chia đều các khung giờ trong ngày
WEEKLY_SCHEDULE: Dict[str, Dict[str, Any]] = {
    "mon": {
        "name": "Thứ 2: Thời cuộc & Quốc tế",
        "slots": {
            "slot1": {
                "time": "02:00",
                "desc": "Thời sự (1 cha + 6 mục con = 7 danh mục)",
                "parents": ["thoi-su"],
            },
            "slot2": {
                "time": "13:00",
                "desc": "Thế giới (1 cha + 6 mục con = 7 danh mục)",
                "parents": ["the-gioi"],
            },
        },
    },
    "tue": {
        "name": "Thứ 3: Kinh tế & Bất động sản",
        "slots": {
            "slot1": {
                "time": "02:00",
                "desc": "Kinh doanh (1 cha + 9 mục con = 10 danh mục)",
                "parents": ["kinh-doanh"],
            },
            "slot2": {
                "time": "13:00",
                "desc": "Bất động sản (1 cha + 6 mục con = 7 danh mục)",
                "parents": ["bat-dong-san"],
            },
        },
    },
    "wed": {
        "name": "Thứ 4: Khoa học Công nghệ & Xe",
        "slots": {
            "slot1": {
                "time": "02:00",
                "desc": "Khoa học Công nghệ (1 cha + 10 mục con = 11 danh mục)",
                "parents": ["khoa-hoc-cong-nghe"],
            },
            "slot2": {
                "time": "13:00",
                "desc": "Xe / Ô tô - Xe máy (1 cha + 8 mục con = 9 danh mục)",
                "parents": ["oto-xe-may"],
            },
        },
    },
    "thu": {
        "name": "Thứ 5: Thể thao, Giải trí & Thư giãn",
        "slots": {
            "slot1": {
                "time": "02:00",
                "desc": "Thể thao (1 cha + 8 mục con = 9 danh mục)",
                "parents": ["the-thao"],
            },
            "slot2": {
                "time": "13:00",
                "desc": "Giải trí (1 cha + 8 mục con = 9 danh mục)",
                "parents": ["giai-tri"],
            },
            "slot3": {
                "time": "20:00",
                "desc": "Thư giãn (1 cha + 6 mục con = 7 danh mục)",
                "parents": ["thu-gian"],
            },
        },
    },
    "fri": {
        "name": "Thứ 6: Sức khỏe, Đời sống & Du lịch",
        "slots": {
            "slot1": {
                "time": "02:00",
                "desc": "Sức khỏe (1 cha + 5 mục con = 6 danh mục)",
                "parents": ["suc-khoe"],
            },
            "slot2": {
                "time": "13:00",
                "desc": "Đời sống (1 cha + 5 mục con = 6 danh mục)",
                "parents": ["doi-song"],
            },
            "slot3": {
                "time": "20:00",
                "desc": "Du lịch (1 cha + 7 mục con = 8 danh mục)",
                "parents": ["du-lich"],
            },
        },
    },
    "sat": {
        "name": "Thứ 7: Giáo dục, Pháp luật, Xã hội & Ý kiến",
        "slots": {
            "slot1": {
                "time": "02:00",
                "desc": "Giáo dục (1 cha + 8 mục con = 9 danh mục)",
                "parents": ["giao-duc"],
            },
            "slot2": {
                "time": "13:00",
                "desc": "Pháp luật & Góc nhìn (2 cha + 10 mục con = 12 danh mục)",
                "parents": ["phap-luat", "goc-nhin"],
            },
            "slot3": {
                "time": "20:00",
                "desc": "Ý kiến & Tâm sự (2 cha + 3 mục con = 5 danh mục)",
                "parents": ["y-kien", "tam-su"],
            },
        },
    },
    "sun": {
        "name": "Chủ nhật: Bảo trì & Đồng bộ tương tác",
        "slots": {
            "slot1": {
                "time": "03:00",
                "desc": "Đồng bộ lượt bình luận thời gian thực cho 500 bài viết gần nhất",
                "parents": [],
            },
            "slot2": {
                "time": "14:00",
                "desc": "Tối ưu hóa Database (SQLite VACUUM) và kiểm tra toàn vẹn",
                "parents": [],
            },
        },
    },
}

# Các nguồn RSS uy tín để lấy 100 tin mới nhất toàn trang
TOP_RSS_FEEDS = [
    "tin-moi-nhat",
    "thoi-su",
    "the-gioi",
    "kinh-doanh",
    "giai-tri",
    "the-thao",
    "phap-luat",
    "giao-duc",
    "suc-khoe",
    "doi-song",
    "du-lich",
    "khoa-hoc",
    "xe",
]


def crawl_100_latest(max_articles: int = 100, proxy_url: Optional[str] = None) -> Dict[str, int]:
    """Crawl 100 latest breaking news across VnExpress RSS feeds."""
    init_db()
    pipeline = ArticlePipeline(proxy_url=proxy_url)
    total_found = 0
    total_new = 0

    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] BẮT ĐẦU CÀO {max_articles} BÀI MỚI NHẤT (RSS BREAKING NEWS)")

    for feed_topic in TOP_RSS_FEEDS:
        remaining = max_articles - total_new
        if remaining <= 0:
            break

        print(f"--> Đang quét RSS '{feed_topic}' (cần thêm tối đa {remaining} bài)...")
        try:
            res = pipeline.crawl_rss(topic=feed_topic, max_articles=remaining)
            total_found += res.get("articles_found", 0)
            total_new += res.get("articles_new", 0)
            print(f"    Tìm thấy: {res.get('articles_found', 0)} bài, Mới: {res.get('articles_new', 0)} bài.")
        except Exception as exc:
            logger.error("Lỗi khi cào RSS '%s': %s", feed_topic, exc)

    print(
        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HOÀN TẤT CÀO TIN MỚI: "
        f"Tổng quét: {total_found} bài, Đã thu nạp mới: {total_new} bài.\n"
    )
    return {"articles_found": total_found, "articles_new": total_new}


def crawl_category_batch(
    parent_slugs: List[str],
    max_articles_per_cat: int = 100,
    max_pages: int = 7,
    delay_between_cats: float = 2.0,
    proxy_url: Optional[str] = None,
) -> Dict[str, int]:
    """Crawl 100 articles for each parent category and 100 articles for each child subcategory."""
    init_db()
    pipeline = ArticlePipeline(proxy_url=proxy_url)

    categories_to_crawl: List[Dict[str, Any]] = []

    with get_db_session() as session:
        repo = Repository(session)
        for pslug in parent_slugs:
            p_cat = repo.get_category_by_slug(pslug)
            if not p_cat:
                logger.warning("Không tìm thấy danh mục cha có slug '%s' trong DB!", pslug)
                continue
            # Mục cha
            categories_to_crawl.append({"id": p_cat.id, "name": p_cat.name, "slug": p_cat.slug, "is_parent": True})
            # Toàn bộ mục con trực thuộc
            children = repo.get_subcategories(p_cat.id)
            for ch in children:
                categories_to_crawl.append({"id": ch.id, "name": ch.name, "slug": ch.slug, "is_parent": False, "parent_name": p_cat.name})

    total_cats = len(categories_to_crawl)
    print(f"\n--- BẮT ĐẦU CÀO BATCH ({total_cats} DANH MỤC, TỐI ĐA {max_articles_per_cat} BÀI/MỤC, MAX {max_pages} TRANG) ---")

    batch_found = 0
    batch_new = 0

    for idx, item in enumerate(categories_to_crawl, start=1):
        c_type = "[MỤC CHA]" if item["is_parent"] else f"[MỤC CON thuộc {item.get('parent_name', '')}]"
        print(f"\n[{idx}/{total_cats}] {c_type} Đang cào '{item['name']}' (/{item['slug']})...")

        try:
            # Crawl non-recursively for exact 100 articles per category
            res = pipeline.crawl_category(
                category_slug=item["slug"],
                max_pages=max_pages,
                max_articles=max_articles_per_cat,
                recursive=False,
            )
            found = res.get("articles_found", 0)
            new_arts = res.get("articles_new", 0)
            batch_found += found
            batch_new += new_arts
            print(f"  -> Hoàn thành: quét {found} bài, thêm mới {new_arts} bài.")
        except Exception as exc:
            logger.error("Lỗi khi cào danh mục %s: %s", item["slug"], exc)
            print(f"  -> Lỗi cào danh mục {item['slug']}: {exc}")

        if idx < total_cats and delay_between_cats > 0:
            time.sleep(delay_between_cats)

    print(
        f"\n--- HOÀN TẤT BATCH {total_cats} DANH MỤC: "
        f"Tổng quét: {batch_found} bài, Tổng nạp mới: {batch_new} bài ---\n"
    )
    return {"articles_found": batch_found, "articles_new": batch_new, "categories_processed": total_cats}


def run_sunday_maintenance(comment_sync_limit: int = 500, proxy_url: Optional[str] = None):
    """Perform Sunday database optimization and comment synchronization."""
    init_db()
    from sqlalchemy import select, text
    import concurrent.futures

    pipeline = ArticlePipeline(proxy_url=proxy_url)
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CHỦ NHẬT: BẢO TRÌ VÀ ĐỒNG BỘ DỮ LIỆU")

    # 1. Update comments
    with get_db_session() as session:
        stmt = select(Article.id, Article.title, Article.comment_count).order_by(Article.published_at.desc().nulls_last()).limit(comment_sync_limit)
        rows = session.execute(stmt).all()
        article_items = [(r[0], r[1], r[2]) for r in rows]

    total_articles = len(article_items)
    print(f"1. Bắt đầu đồng bộ lượt bình luận cho {total_articles} bài viết gần nhất...")

    def fetch_one(item):
        aid, title, old_c = item
        live_c = pipeline.fetch_live_comment_count(aid)
        return aid, live_c, old_c

    updated_count = 0
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for idx, (aid, live_c, old_c) in enumerate(executor.map(fetch_one, article_items), 1):
            results.append((aid, live_c))
            if live_c > 0 and live_c != old_c:
                updated_count += 1
            if idx % 50 == 0 or idx == total_articles:
                print(f"   Đã quét {idx}/{total_articles} bài ({updated_count} bài có bình luận mới)...")

    with get_db_session() as session:
        for aid, live_c in results:
            if live_c > 0:
                art = session.get(Article, aid)
                if art:
                    art.comment_count = live_c

    print(f"   -> Đã cập nhật số lượng bình luận cho {updated_count}/{total_articles} bài.")

    # 2. Backfill missing media & rich metadata
    print("2. Đang quét và bổ sung media / rich metadata cho các bài viết cũ...")
    try:
        from crawler.pipeline.article_backfill import ArticleBackfillPipeline

        bf_pipeline = ArticleBackfillPipeline(proxy_url=proxy_url)
        bf_res = bf_pipeline.backfill_missing_media(limit=50, delay=0.2)
        print(f"   -> Đã bổ sung media cho {bf_res['updated']} bài viết thiếu ảnh.")
    except Exception as exc:
        print(f"   -> Lỗi khi chạy backfill bảo trì: {exc}")

    # 3. SQLite VACUUM & ANALYZE
    print("3. Đang tối ưu hóa lưu trữ SQLite (VACUUM & ANALYZE)...")
    try:
        with get_db_session() as session:
            session.execute(text("VACUUM"))
            session.execute(text("ANALYZE"))
        print("   -> Tối ưu hóa Database thành công.")
    except Exception as exc:
        print(f"   -> Không thể VACUUM database: {exc}")

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] BẢO TRÌ HOÀN TẤT.\n")


def get_current_day_key() -> str:
    """Return lowercase 3-letter day key: mon, tue, wed, thu, fri, sat, sun."""
    return datetime.datetime.now().strftime("%a").lower()[:3]


def run_daily_job(
    day_key: Optional[str] = None,
    slot_key: Optional[str] = None,
    max_articles: int = 100,
    max_pages: int = 7,
    proxy_url: Optional[str] = None,
):
    """Run scheduled category batches for a specific day and slot."""
    if not day_key or day_key == "today":
        day_key = get_current_day_key()
    else:
        day_key = day_key.lower().strip()[:3]

    if day_key not in WEEKLY_SCHEDULE:
        print(f"Lỗi: Mã ngày '{day_key}' không hợp lệ. Chọn: mon, tue, wed, thu, fri, sat, sun.")
        sys.exit(1)

    sched = WEEKLY_SCHEDULE[day_key]
    print(f"\n==================================================================")
    print(f" LỊCH TRÌNH NGÀY: {sched['name'].upper()}")
    print(f" Thời gian thực thi: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"==================================================================")

    if day_key == "sun":
        if slot_key == "slot2":
            print("Chạy Slot 2 Chủ Nhật: Tối ưu hóa Database...")
            with get_db_session() as session:
                from sqlalchemy import text
                session.execute(text("VACUUM"))
                session.execute(text("ANALYZE"))
            print("Hoàn tất tối ưu hóa Database.")
        else:
            run_sunday_maintenance(comment_sync_limit=500, proxy_url=proxy_url)
        return

    slots = sched["slots"]
    if slot_key:
        slot_key = slot_key.lower().strip()
        if slot_key not in slots:
            print(f"Lỗi: Khung giờ '{slot_key}' không tồn tại cho ngày {day_key}. Có sẵn: {list(slots.keys())}")
            sys.exit(1)
        target_slots = {slot_key: slots[slot_key]}
    else:
        target_slots = slots

    for s_name, s_info in target_slots.items():
        print(f"\n>>> Thực thi {s_name.upper()} ({s_info['time']}): {s_info['desc']}")
        crawl_category_batch(
            parent_slugs=s_info["parents"],
            max_articles_per_cat=max_articles,
            max_pages=max_pages,
            proxy_url=proxy_url,
        )


def run_all_categories(max_articles: int = 100, max_pages: int = 7, proxy_url: Optional[str] = None):
    """Run sequential crawl for all 122 categories in system."""
    all_parents = []
    for day_data in WEEKLY_SCHEDULE.values():
        for slot in day_data.get("slots", {}).values():
            all_parents.extend(slot.get("parents", []))

    print(f"\nKÍCH HOẠT QUÉT TOÀN DIỆN TẤT CẢ DANH MỤC TRONG HỆ THỐNG ({len(all_parents)} cụm cha)...")
    crawl_category_batch(
        parent_slugs=all_parents,
        max_articles_per_cat=max_articles,
        max_pages=max_pages,
        proxy_url=proxy_url,
    )


def print_weekly_plan():
    """Print the complete formatted weekly distribution table."""
    init_db()
    with get_db_session() as session:
        repo = Repository(session)
        all_cats = repo.get_all_categories()
        total_cats_db = len(all_cats)

    print("\n" + "=" * 78)
    print(" BẢNG PHÂN CHIA LỊCH CÀO TIN HẰNG TUẦN (TỔNG SỐ 122 DANH MỤC - VNEXPRESS)")
    print("=" * 78)

    total_accounted = 0
    for day_code, info in WEEKLY_SCHEDULE.items():
        print(f"\n📅 [{day_code.upper()}] {info['name']}")
        slots = info["slots"]
        for s_code, s_data in slots.items():
            parent_list = s_data["parents"]
            sub_count = 0
            with get_db_session() as session:
                repo = Repository(session)
                for pslug in parent_list:
                    p = repo.get_category_by_slug(pslug)
                    if p:
                        subs = repo.get_subcategories(p.id)
                        sub_count += 1 + len(subs)
            total_accounted += sub_count
            cat_str = f"({sub_count} danh mục)" if sub_count > 0 else "(Bảo trì)"
            print(f"   ⏰ {s_data['time']} [{s_code}] -> {s_data['desc']} {cat_str}")

    print("\n" + "=" * 78)
    print(f" Tổng danh mục được lập lịch: {total_accounted} / {total_cats_db} danh mục.")
    print(" Lịch 100 tin mới nhất (Breaking RSS): Chạy mỗi giờ (00 phút: 0 * * * *)")
    print("=" * 78 + "\n")


def main_cli(args):
    proxy_url = getattr(args, "proxy", None)
    if args.mode == "schedule":
        print_weekly_plan()
    elif args.mode == "hourly":
        crawl_100_latest(max_articles=args.max_articles, proxy_url=proxy_url)
    elif args.mode == "daily":
        run_daily_job(
            day_key=args.day,
            slot_key=args.slot,
            max_articles=args.max_articles,
            max_pages=args.pages,
            proxy_url=proxy_url,
        )
    elif args.mode == "maintenance":
        run_sunday_maintenance(proxy_url=proxy_url)
    elif args.mode == "all":
        run_all_categories(
            max_articles=args.max_articles,
            max_pages=args.pages,
            proxy_url=proxy_url,
        )


def main():
    parser = argparse.ArgumentParser(
        description="VnExpress News Aggregator - Weekly Cronjob Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["hourly", "daily", "all", "maintenance", "schedule"],
        default="daily",
        help="Chế độ thực thi: hourly (100 tin mới), daily (theo ngày), all (tất cả 122 mục), maintenance (bảo trì), schedule (xem lịch)",
    )
    parser.add_argument(
        "--day",
        choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun", "today"],
        default="today",
        help="Thứ trong tuần (dùng cho chế độ daily)",
    )
    parser.add_argument(
        "--slot",
        choices=["slot1", "slot2", "slot3"],
        default=None,
        help="Khung giờ cụ thể trong ngày (slot1, slot2, slot3). Mặc định chạy hết các slot của ngày.",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=100,
        help="Số bài viết mới tối đa cho mỗi danh mục hoặc bài mới nhất",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=7,
        help="Số trang danh mục tối đa cần duyệt (mỗi trang ~15-20 bài)",
    )
    parser.add_argument(
        "--proxy",
        "-p",
        default=None,
        help="Địa chỉ Proxy (HTTP/HTTPS hoặc SOCKS5, vd: socks5://127.0.0.1:40000, http://user:pass@ip:port)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    main_cli(args)


if __name__ == "__main__":
    main()
