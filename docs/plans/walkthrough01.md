# Báo Cáo Triển Khai & Nghiệm Thu Giai Đoạn 1: Crawler Core

Hệ thống **Crawler Core** cho nền tảng tổng hợp tin tức tự động VnExpress (VnExpress News Aggregator) đã được xây dựng và kiểm thử thành công theo đúng đặc tả kỹ thuật trong [docs/GUIDE.md](file:///home/vvx/Documents/life_it_antigravity/crawl_news/docs/GUIDE.md) và cấu trúc thực tế tại [docs/vn-express.md](file:///home/vvx/Documents/life_it_antigravity/crawl_news/docs/vn-express.md).

---

## 1. Các thành phần đã triển khai

### 1.1. Cấu hình & Môi trường
- [requirements.txt](file:///home/vvx/Documents/life_it_antigravity/crawl_news/requirements.txt): Danh mục thư viện (`httpx[http2]`, `h2`, `beautifulsoup4`, `lxml`, `pydantic-settings`, `sqlalchemy`, `redis`, `pytest`).
- [.env.example](file:///home/vvx/Documents/life_it_antigravity/crawl_news/.env.example): Mẫu cấu hình môi trường linh hoạt cho SQLite/PostgreSQL, Redis, delay và rate limit.
- [crawler/config.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/config.py): Quản lý cấu hình bằng Pydantic `Settings`.

### 1.2. HTTP Engine & Anti-blocking
- [crawler/http_client.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/http_client.py):
  - Client HTTP/2 bọc `httpx` (hỗ trợ cả đồng bộ và bất đồng bộ).
  - Luân phiên User-Agent hiện đại (Chrome, Firefox, Safari) và bộ header chuẩn trình duyệt.
  - Cơ chế giãn cách ngẫu nhiên `DOWNLOAD_DELAY = 0.5s - 1.0s` với jitter.
  - Tự động Retry với exponential backoff khi gặp sự cố mạng hoặc mã lỗi 429/5xx.

### 1.3. Cơ sở dữ liệu & Lưu trữ
- [crawler/storage/models.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/storage/models.py): Khởi tạo 4 thực thể quan hệ chuẩn Clean Architecture:
  - `Category`: Quản lý danh mục đa cấp (hỗ trợ cha - con đệ quy với `parent_id`).
  - `Article`: Bài viết với đầy đủ metadata, `content_html` sạch, `content_text` cho tìm kiếm, ngày xuất bản và tác giả.
  - `Media`: Danh sách ảnh/video gắn với bài viết, caption, kích thước, local path.
  - `CrawlLog`: Lưu vết tiến trình cào dữ liệu, số lượng bài tìm thấy, bài mới, trạng thái lỗi.
- [crawler/storage/database.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/storage/database.py): Quản lý kết nối, tự động khởi tạo bảng.
- [crawler/storage/repository.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/storage/repository.py): Lớp truy cập dữ liệu (CRUD, lọc theo danh mục, thống kê).

### 1.4. Bộ lọc trùng lặp (Deduplication)
- [crawler/deduplicator.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/deduplicator.py):
  - Hỗ trợ `RedisDeduplicator` sử dụng Redis Set (`SADD`, `SISMEMBER`, pipeline).
  - Tự động fallback sang `LocalDeduplicator` và nạp trước toàn bộ ID đã có trong cơ sở dữ liệu khi chưa bật Redis service, đảm bảo không bao giờ cào lại bài cũ.

### 1.5. Hệ thống Parsers
- [crawler/parsers/category.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/parsers/category.py): Bóc tách menu danh mục cấp 1 và toàn bộ thư mục con từ `ul.ul-nav-folder`.
- [crawler/parsers/listing.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/parsers/listing.py): Xử lý trích xuất bài viết và phân trang:
  - Tương thích định dạng đa container của Trang 1 (`news-container01-04`, `container-top-header`).
  - Tương thích định dạng Trang 2-20 (`news-container-page2-20`).
  - Sinh dải link phân trang `-p2` đến `-p20`.
- [crawler/parsers/rss.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/parsers/rss.py): Bóc tách tin mới tức thì từ XML RSS của VnExpress.
- [crawler/parsers/article.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/parsers/article.py): Bóc tách chi tiết bài viết, làm sạch mã HTML (loại bỏ quảng cáo `banner-ads`, tracking, popup), trích xuất ảnh `<figure>` cùng chú thích và tên tác giả.

### 1.6. Pipelines & CLI
- [crawler/pipeline/category_sync.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/pipeline/category_sync.py): Pipeline đồng bộ toàn bộ cây danh mục tự động.
- [crawler/pipeline/article_pipeline.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/pipeline/article_pipeline.py): Điều phối thu thập danh sách -> lọc trùng -> tải chi tiết -> lưu DB.
- [crawler/cli.py](file:///home/vvx/Documents/life_it_antigravity/crawl_news/crawler/cli.py): CLI thân thiện với đầy đủ chức năng.

---

## 2. Kết quả Kiểm thử Tự động (Unit Tests)

Chạy kiểm thử toàn bộ test suite bằng `pytest`:
```bash
./.venv/bin/pytest tests/ -v
```

**Kết quả:**
```
============================= test session starts ==============================
collected 13 items

tests/test_article_parser.py::test_parse_article_details PASSED          [  7%]
tests/test_category_parser.py::test_parse_main_categories PASSED         [ 15%]
tests/test_category_parser.py::test_parse_sub_categories PASSED          [ 23%]
tests/test_deduplication.py::test_local_deduplicator_lifecycle PASSED    [ 30%]
tests/test_deduplication.py::test_get_deduplicator_fallback PASSED       [ 38%]
tests/test_listing_parser.py::test_parse_listing_page2_20 PASSED         [ 46%]
tests/test_listing_parser.py::test_parse_listing_container_top_header PASSED [ 53%]
tests/test_listing_parser.py::test_parse_listing_container02 PASSED      [ 61%]
tests/test_listing_parser.py::test_generate_category_page_urls PASSED    [ 69%]
tests/test_rss_parser.py::test_parse_rss PASSED                          [ 76%]
tests/test_storage.py::test_category_crud PASSED                         [ 84%]
tests/test_storage.py::test_article_and_media_crud PASSED                [ 92%]
tests/test_storage.py::test_crawl_logs_and_stats PASSED                  [100%]

============================== 13 passed in 0.77s ==============================
```

---

## 3. Kết quả Thực thi Thực tế trên VnExpress (Live Verification)

### 3.1. Đồng bộ danh mục (`sync-categories`)
- Quét trang chủ và từng chuyên mục cấp 1:
- Đã đồng bộ thành công: **17 danh mục cha** và **105 danh mục con** (tổng cộng 122 danh mục).
- Dưới chuyên mục `Khoa học công nghệ` (`/khoa-hoc-cong-nghe`), hệ thống nhận diện đầy đủ 10 chuyên mục con đúng theo bảng trong tài liệu khảo sát `docs/vn-express.md`:
  - `AI` (`/khoa-hoc-cong-nghe/ai`)
  - `AI4VN` (`/khoa-hoc-cong-nghe/ai4vn-2026`)
  - `Chuyển đổi số` (`/khoa-hoc-cong-nghe/chuyen-doi-so`)
  - `Hoạt động Bộ KH&CN` (`/khoa-hoc-cong-nghe/bo-khoa-hoc-va-cong-nghe`)
  - `Sáng kiến khoa học` (`/khoa-hoc-cong-nghe/cuoc-thi-sang-kien-khoa-hoc`)
  - `Tech Awards` (`/khoa-hoc-cong-nghe/tech-awards`)
  - `Thiết bị` (`/khoa-hoc-cong-nghe/thiet-bi`)
  - `Thế giới tự nhiên` (`/khoa-hoc-cong-nghe/the-gioi-tu-nhien`)
  - `Vũ trụ` (`/khoa-hoc-cong-nghe/vu-tru`)
  - `Đổi mới sáng tạo` (`/khoa-hoc-cong-nghe/doi-moi-sang-tao`)

### 3.2. Cào bài viết chuyên mục & Cơ chế lọc trùng (`crawl-category`)
- Lần 1: Cào 3 bài từ chuyên mục `khoa-hoc-cong-nghe` -> Hệ thống tìm thấy 48 bài viết, thu thập mới 3 bài.
- Lần 2: Tiếp tục chạy cào 3 bài -> Hệ thống tự động phát hiện `45 new, 3 already seen`, bỏ qua 3 bài cũ và tiếp tục thu thập 3 bài tiếp theo mà không bị trùng lặp!

### 3.3. Cào tin mới qua RSS (`crawl-rss`)
- Cào từ `https://vnexpress.net/rss/tin-moi-nhat.rss`:
- Bóc tách thành công các bài viết mới nhất tức thì.

### 3.4. Cào bài viết đơn lẻ (`crawl-article`)
- Thực nghiệm với bài: `https://vnexpress.net/video-ngan-tu-youtuber-viet-tang-hon-100-sau-mot-nam-5121093.html`
- Kết quả trích xuất:
  - ID: `5121093`
  - Tiêu đề: `Video ngắn từ YouTuber Việt tăng hơn 100% sau một năm`
  - Tác giả: `Lưu Quý`
  - Ngày xuất bản: `2026-09-17 07:31:35+07:00`
  - Chuyên mục: `khoa-hoc-cong-nghe/chuyen-doi-so/nhip-song-so`
  - Ảnh + Caption: Trích xuất đầy đủ vào bảng `media`.
  - Nội dung HTML sạch: 2683 ký tự text, không chứa script hay quảng cáo.

### 3.5. Thống kê hệ thống hiện tại (`stats`)
```
================ THỐNG KÊ CRAWLER CORE ================
 Tổng số danh mục:      122
 Tổng số bài viết:      10
 Tổng số file media:    30
 Số ID đã lưu lọc trùng:10
========================================================
```

---

## 4. Hướng dẫn sử dụng CLI

```bash
# Xem danh sách các lệnh
./.venv/bin/python3 -m crawler.cli --help

# Xem cây danh mục hiện có
./.venv/bin/python3 -m crawler.cli list-categories

# Đồng bộ lại cây danh mục
./.venv/bin/python3 -m crawler.cli sync-categories

# Cào chuyên mục với số trang tùy chọn (vd: 2 trang đầu)
./.venv/bin/python3 -m crawler.cli crawl-category khoa-hoc-cong-nghe --pages 2 --max-articles 10

# Cào tin mới nhất từ RSS
./.venv/bin/python3 -m crawler.cli crawl-rss --max-articles 5

# Cào chi tiết một bài viết cụ thể
./.venv/bin/python3 -m crawler.cli crawl-article <URL_BAI_VIET>

# Xem thống kê số lượng bài viết và nhật ký cào
./.venv/bin/python3 -m crawler.cli stats
```
