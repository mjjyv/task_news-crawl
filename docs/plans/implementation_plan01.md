# Kế hoạch Triển khai Giai đoạn 1: Crawler Core (VnExpress News Aggregator)

Tài liệu này đặc tả kiến trúc, thiết kế kỹ thuật và lộ trình triển khai chi tiết cho **Giai đoạn 1: Khảo sát & Xây dựng Crawler Core** dựa trên hai tài liệu nền tảng:
- [`docs/GUIDE.md`](file:///home/vvx/Documents/life_it_antigravity/crawl_news/docs/GUIDE.md): Đặc tả kỹ thuật và kiến trúc hệ thống 4 giai đoạn.
- [`docs/vn-express.md`](file:///home/vvx/Documents/life_it_antigravity/crawl_news/docs/vn-express.md): Khảo sát thực tế cấu trúc chuyên mục, danh mục cha-con, quy tắc phân trang (Page 1 đến Page 20) và các mẫu DOM HTML (`news-container01-04`, `news-container-page2-20`).

---

## 1. Mục tiêu Giai đoạn 1

Xây dựng module Crawler Core hoàn chỉnh bằng Python, có độ tin cậy cao, kiến trúc module hóa sạch sẽ (Clean Architecture), bao gồm:
1. **Engine HTTP & Anti-blocking**:
   - `httpx` async & sync client.
   - Luân phiên User-Agent (modern Chrome, Firefox, Safari).
   - Cơ chế giãn cách (`DOWNLOAD_DELAY = 0.5s - 1.0s` có jitter ngẫu nhiên).
   - Tự động Retry với exponential backoff khi gặp sự cố mạng hoặc 429/5xx.
2. **Hệ thống Parsers chuyên biệt**:
   - `CategoryParser`: Tự động thu thập cây danh mục cha và con từ VnExpress (`/thoi-su`, `/khoa-hoc-cong-nghe/...`).
   - `ListingParser`: Trích xuất danh sách bài viết từ trang chuyên mục (hỗ trợ Page 1 đa container `news-container01-04` và Page 2–20 `news-container-page2-20`), trích xuất link dạng `.*-(\d+)\.html`.
   - `RSSParser`: Thu thập tin tức mới nhất tức thì từ VnExpress RSS feeds (`/rss/*.rss`).
   - `ArticleDetailParser`: Trích xuất toàn diện bài viết (tiêu đề, sapo, ngày xuất bản, tác giả, danh mục, breadcrumbs, nội dung HTML sạch loại bỏ quảng cáo, nội dung text cho tìm kiếm, media ảnh + caption, video).
3. **Cơ chế Khử trùng lặp (Deduplication)**:
   - Lọc trùng theo `article_id` bằng Redis Set (theo đặc tả).
   - Hỗ trợ fallback cục bộ (Memory/SQLite) khi chạy môi trường dev/test không có Redis server.
4. **Cơ sở dữ liệu & Lưu trữ (Storage)**:
   - SQLAlchemy ORM hỗ trợ PostgreSQL (chuẩn sản xuất) và SQLite (môi trường dev/test không cần cài đặt phức tạp).
   - Schema chuẩn: `categories`, `articles`, `media`, `crawl_logs`.
5. **Giao diện dòng lệnh (CLI)**:
   - Lệnh sync danh mục: `python -m crawler.cli sync-categories`
   - Lệnh crawl chuyên mục: `python -m crawler.cli crawl-category <slug> [--pages 20]`
   - Lệnh crawl RSS: `python -m crawler.cli crawl-rss`
   - Lệnh crawl chi tiết bài: `python -m crawler.cli crawl-articles [--limit 50]`
   - Lệnh thống kê: `python -m crawler.cli stats`
6. **Kiểm thử tự động (Unit Tests & Integration Tests)**:
   - Bộ test chạy bằng `pytest` kiểm tra tính chính xác của các parser với các mẫu HTML thực tế có sẵn trong thư mục `docs/`.

---

## 2. Thiết kế Kiến trúc & Cấu trúc Thư mục

```
crawl_news/
├── .env.example                  # Mẫu cấu hình môi trường (DB, Redis, Crawl delay)
├── requirements.txt              # Danh sách thư viện Python
├── docs/                         # Tài liệu và mẫu HTML của dự án
│   ├── GUIDE.md
│   ├── vn-express.md
│   ├── container-top-header.html
│   ├── news-container-page2-20.html
│   └── news-container01.html ...
├── crawler/
│   ├── __init__.py
│   ├── config.py                 # Cấu hình Pydantic Settings
│   ├── http_client.py            # HTTP Client bọc httpx, rotating UA, retry, rate limit
│   ├── deduplicator.py           # Deduplicator (Redis Set + Memory/SQLite fallback)
│   ├── cli.py                    # CLI điều khiển crawler
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py               # Interface parser chuẩn
│   │   ├── category.py           # Parser danh mục cha & con
│   │   ├── listing.py            # Parser trang danh sách (Page 1 và Page 2-20)
│   │   ├── article.py            # Parser chi tiết bài viết (text, photo, video)
│   │   └── rss.py                # Parser nguồn RSS
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py           # SQLAlchemy engine & session management
│   │   ├── models.py             # ORM models (Category, Article, Media, CrawlLog)
│   │   └── repository.py         # Data Access Layer
│   └── pipeline/
│       ├── __init__.py
│       ├── category_sync.py      # Pipeline đồng bộ danh mục
│       └── article_pipeline.py   # Pipeline crawl bài viết (Fetch -> Deduplicate -> Parse -> Save)
└── tests/
    ├── __init__.py
    ├── test_category_parser.py   # Test bóc tách cây danh mục
    ├── test_listing_parser.py    # Test bóc tách link từ file HTML mẫu
    ├── test_article_parser.py    # Test bóc tách bài viết chi tiết
    ├── test_rss_parser.py        # Test bóc tách feed RSS
    ├── test_deduplication.py     # Test bộ lọc trùng Redis/Memory
    └── test_storage.py           # Test lưu trữ cơ sở dữ liệu
```

---

## 3. Thiết kế Cơ sở Dữ liệu & Schemas

### Bảng `categories`
- `id`: Integer primary key (hoặc auto-increment)
- `name`: String(255)
- `slug`: String(255) unique (ví dụ: `khoa-hoc-cong-nghe`, `khoa-hoc-cong-nghe/ai`)
- `parent_id`: Integer ForeignKey(`categories.id`, ondelete="CASCADE"), nullable
- `origin_url`: String(500)
- `description`: Text, nullable

### Bảng `articles`
- `id`: BigInteger primary key (ID bài báo VnExpress, ví dụ `5121093`)
- `title`: String(500)
- `slug`: String(500)
- `description`: Text (sapo tóm tắt)
- `content_html`: Text (HTML đã qua xử lý lọc sạch rác quảng cáo)
- `content_text`: Text (plain text không chứa HTML tag để phục vụ tìm kiếm)
- `author`: String(255), nullable
- `thumbnail_url`: String(500), nullable
- `origin_url`: String(500) unique
- `category_id`: Integer ForeignKey(`categories.id`), nullable
- `published_at`: DateTime(timezone=True)
- `created_at`: DateTime(timezone=True)

### Bảng `media`
- `id`: Integer primary key auto-increment
- `article_id`: BigInteger ForeignKey(`articles.id`, ondelete="CASCADE")
- `type`: String(20) (`image` hoặc `video`)
- `url`: String(1000)
- `caption`: Text, nullable
- `width`: Integer, nullable
- `height`: Integer, nullable
- `local_path`: String(500), nullable

### Bảng `crawl_logs`
- `id`: Integer primary key auto-increment
- `crawler_type`: String(50) (`category_sync`, `listing`, `rss`, `article_detail`)
- `target_url`: String(500)
- `status`: String(20) (`success`, `failed`, `skipped`)
- `articles_found`: Integer default 0
- `articles_new`: Integer default 0
- `error_message`: Text, nullable
- `executed_at`: DateTime(timezone=True)

---

## 4. User Review Required

> [!IMPORTANT]
> **Phương án kết nối Database & Redis trong môi trường phát triển hiện tại:**
> Hiện tại trên máy host chưa có PostgreSQL và Redis service chạy nền, Docker socket cần quyền hạn truy cập của user. Do đó, Crawler Core được thiết kế để:
> - Sử dụng SQLAlchemy: mặc định dùng `sqlite:///news.db` cho dev/test và sẵn sàng cấu hình sang `postgresql://...` thông qua biến môi trường `.env` mà không phải thay đổi một dòng code nào.
> - Sử dụng Deduplicator: nếu Redis đang chạy (kết nối thành công), hệ thống sẽ dùng Redis Set; nếu Redis chưa bật, hệ thống tự động fallback sang SQLite/Memory Set, ghi log cảnh báo rõ ràng.
> Bạn có đồng ý với cơ chế linh hoạt này không?

> [!NOTE]
> **Phương án lưu Media (Ảnh/Video):**
> Theo mục 8 trong `GUIDE.md`:
> - Phương án 1: Lưu URL ảnh trực tiếp từ CDN VnExpress (nhẹ, nhanh, phù hợp Phase 1).
> - Phương án 2: Tải toàn bộ file ảnh về ổ cứng cục bộ/S3.
> Trong Giai đoạn 1, chúng tôi sẽ trích xuất và lưu đầy đủ URL ảnh + caption + metadata vào bảng `media`, đồng thời chuẩn bị sẵn hook `download_media` để có thể kích hoạt tải file về ổ đĩa khi cần.

---

## 5. Kế hoạch triển khai chi tiết các bước (Giai đoạn 1)

### Bước 1: Cấu hình môi trường & Settings
- Tạo `requirements.txt` và file `.env.example`.
- Viết `crawler/config.py` sử dụng Pydantic BaseSettings quản lý cấu hình: delay, user-agent pool, timeout, db_url, redis_url.

### Bước 2: Xây dựng HTTP Client & Anti-blocking
- Viết `crawler/http_client.py`:
  - Quản lý session `httpx.Client` / `httpx.AsyncClient`.
  - Rotating User-Agent hợp lệ (desktop browsers).
  - Tự động áp dụng headers phù hợp (Accept, Accept-Language, Sec-Ch-Ua).
  - Exponential backoff retry khi lỗi mạng hoặc mã trạng thái 429/500/502/503.
  - Delay ngẫu nhiên giữa các request: `0.5s - 1.0s`.

### Bước 3: Xây dựng Storage & Deduplication Engine
- Viết `crawler/storage/models.py`: Định nghĩa các bảng `categories`, `articles`, `media`, `crawl_logs`.
- Viết `crawler/storage/database.py`: Quản lý engine, session, khởi tạo schema.
- Viết `crawler/storage/repository.py`: Các hàm CRUD bài viết, danh mục, media, log.
- Viết `crawler/deduplicator.py`: Lớp trừu tượng `Deduplicator` với `RedisDeduplicator` và `LocalDeduplicator` lọc trùng `article_id`.

### Bước 4: Xây dựng Bộ Parsers (Core)
- Viết `crawler/parsers/category.py`: Bóc tách toàn bộ danh mục cấp 1 từ menu chính và các danh mục con từ `ul.ul-nav-folder`.
- Viết `crawler/parsers/listing.py`: Bóc tách link bài viết `https://vnexpress.net/<slug>-<id>.html`:
  - Xử lý các container trang 1: `container-top-header.html`, `news-container01.html`, `news-container02.html`, `news-container03.html`, `news-container04.html`.
  - Xử lý container trang 2-20: `news-container-page2-20.html`.
  - Trích xuất `article_id`, `url`, `thumbnail`, `title`, `sapo`.
- Viết `crawler/parsers/rss.py`: Bóc tách tin mới từ RSS XML của VnExpress (`/rss/*.rss`).
- Viết `crawler/parsers/article.py`: Bóc tách chi tiết bài viết:
  - Text detail: `h1.title-detail`, `p.description`, `article.fck_detail`, `span.date`.
  - Tách ảnh (`<figure>`, `<picture>`, `data-src`, `figcaption`).
  - Lấy tên tác giả (cuối bài `p.Normal strong` hoặc `p.author`).
  - Làm sạch HTML loại bỏ banner ads, script, social widgets.

### Bước 5: Xây dựng Pipelines & CLI điều khiển
- Viết `crawler/pipeline/category_sync.py`: Đồng bộ danh mục vào database.
- Viết `crawler/pipeline/article_pipeline.py`: Luồng thu thập link -> lọc trùng -> tải nội dung chi tiết -> lưu DB và media.
- Viết `crawler/cli.py`: CLI thân thiện hỗ trợ đầy đủ các lệnh cào dữ liệu, kiểm tra trạng thái và thống kê.

### Bước 6: Kiểm thử tự động (Unit Tests)
- Viết các file test trong `tests/` kiểm thử parser với dữ liệu offline từ các file mẫu trong `docs/`:
  - `test_listing_parser.py`: Kiểm thử với `docs/news-container-page2-20.html` và `docs/news-container01-04.html`.
  - `test_category_parser.py`: Kiểm thử bóc tách menu danh mục.
  - `test_article_parser.py`: Kiểm thử trích xuất nội dung bài viết, hình ảnh, tác giả.
  - `test_deduplication.py`: Kiểm thử cơ chế lọc trùng ID.
  - `test_storage.py`: Kiểm thử lưu trữ cơ sở dữ liệu.
- Chạy `pytest` đảm bảo 100% test case vượt qua.

---

## 6. Kế hoạch Kiểm tra (Verification Plan)

### Automated Tests
```bash
# Chạy toàn bộ test suite
./.venv/bin/pytest tests/ -v
```

### Manual Verification
1. **Kiểm tra đồng bộ danh mục**:
   ```bash
   ./.venv/bin/python -m crawler.cli sync-categories
   ```
   Kiểm tra danh mục cha và con được lưu chính xác vào database.
2. **Kiểm tra cào trang chuyên mục & lọc trùng**:
   ```bash
   ./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe --pages 2
   ```
   Kiểm tra danh sách bài viết được thu thập, trích xuất ID chính xác, không bị trùng lặp.
3. **Kiểm tra cào chi tiết bài viết**:
   ```bash
   ./.venv/bin/python -m crawler.cli crawl-articles --limit 5
   ```
   Kiểm tra nội dung `content_html`, `content_text`, `author`, `published_at`, `media` lưu vào database.
4. **Kiểm tra thống kê**:
   ```bash
   ./.venv/bin/python -m crawler.cli stats
   ```
