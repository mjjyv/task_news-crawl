# ĐẶC TẢ KỸ THUẬT & KẾ HOẠCH TRIỂN KHAI  
## DỰ ÁN: HỆ THỐNG THU THẬP, LƯU TRỮ VÀ HIỂN THỊ TIN TỨC TỰ ĐỘNG (NEWS AGGREGATOR)

---

## 1. Tổng quan dự án

Mục tiêu của dự án là xây dựng một nền tảng đọc báo cá nhân hóa, có khả năng tự động thu thập, chuẩn hóa, lưu trữ và hiển thị tin tức từ VnExpress. Hệ thống hướng tới trải nghiệm đọc tin tối giản, không quảng cáo, tốc độ tải nhanh, hỗ trợ tìm kiếm và tra cứu bài viết hiệu quả.

Dự án tập trung vào hai trụ cột chính:

1. **Data Ingestion & Processing:** Crawler mạnh mẽ, chịu lỗi tốt, cào chính xác nội dung, định dạng và media.
2. **Backend & Presentation:** API chuẩn RESTful/GraphQL, cơ sở dữ liệu phân tầng, giao diện đọc tin tối giản và tối ưu tốc độ.

Dự án có độ phức tạp trung bình và hoàn toàn khả thi. Cấu trúc URL, DOM và RSS của VnExpress có tính đồng nhất cao; phần lớn nội dung được render sẵn phía server, không đòi hỏi render JavaScript phức tạp.

---

## 2. Phạm vi yêu cầu kỹ thuật

Hệ thống được chia thành 4 phân hệ chính:

### 2.1. Phân hệ Crawler & Worker

**Nguồn dữ liệu:**
- Chuyên mục và bài viết trên VnExpress.
- Ưu tiên RSS feed để phát hiện bài mới.
- Kết hợp crawler chuyên sâu cho bài viết chi tiết và dữ liệu lịch sử.

**Trường dữ liệu cần trích xuất:**
- Metadata: tiêu đề, tóm tắt/sapo, tác giả, ngày giờ xuất bản, chuyên mục/tags, URL gốc.
- Nội dung chính: toàn bộ body text, giữ nguyên định dạng đoạn văn, blockquote.
- Media: danh sách ảnh/video, URL gốc, caption; tải về lưu trữ cục bộ/S3 nếu cần đọc ngoại tuyến.

**Cơ chế hoạt động:**
- Cào định kỳ bằng Cron job/Scheduler cho bài mới.
- Cào vét batch cho dữ liệu bài cũ/lịch sử.
- Chống chặn: rate limiting, User-Agent rotation, retry khi request lỗi.
- Khử trùng lặp dựa trên ID bài viết hoặc hash URL.
- Sử dụng Redis Set để lọc trùng article_id trước khi đẩy vào hàng đợi crawl chi tiết.

**Đặc điểm kỹ thuật của VnExpress:**
- URL bài viết dạng: `<slug>-<id>.html`.
- Phân trang dạng tham số đuôi: `-p2` đến `-p20`.
- Nội dung chủ yếu là SSR/Static HTML.
- Selector tham khảo:
  - Tiêu đề: `h1.title-detail`
  - Mô tả: `p.description`
  - Nội dung chính: `article.fck_detail`
  - Thời gian: `span.date`

---

### 2.2. Phân hệ Cơ sở dữ liệu & Tìm kiếm

**Relational Database:**
- Quản lý cấu trúc bài viết, metadata, quan hệ giữa categories, tags và logs cào dữ liệu.
- Đề xuất: PostgreSQL.

**Search Engine:**
- Tích hợp Full-Text Search hỗ trợ tiếng Việt có dấu/không dấu.
- PostgreSQL có thể dùng `pg_trgm` và Full-Text Search cho quy mô vừa và nhỏ.
- Khi dữ liệu lớn hơn, có thể mở rộng sang Meilisearch hoặc Elasticsearch để tăng tốc tìm kiếm, hỗ trợ typo-tolerant.

---

### 2.3. Phân hệ Backend API

- Kiến trúc module hóa theo Clean Architecture hoặc Hexagonal Architecture.
- Cung cấp API phục vụ:
  - Lấy danh sách bài viết theo chuyên mục, phân trang, lọc theo mốc thời gian.
  - Xem chi tiết bài viết.
  - Tìm kiếm nâng cao.
  - Dashboard quản lý tiến trình cào và tình trạng dữ liệu.
- RESTful là lựa chọn chính; GraphQL có thể bổ sung nếu cần.

**API dự kiến:**
- `GET /categories` – lấy cây danh mục.
- `GET /articles?category=...&page=...` – danh sách bài viết theo chuyên mục.
- `GET /articles/{id}` – chi tiết bài viết.
- `GET /search?q=...` – tìm kiếm full-text.
- `GET /crawler/health` – kiểm tra trạng thái crawler.

---

### 2.4. Phân hệ Giao diện

- Giao diện đọc tin tối giản, không quảng cáo, tối ưu trải nghiệm đọc.
- Tốc độ tải trang tức thì.
- Hỗ trợ Dark/Light mode.
- Thiết kế responsive cho Desktop & Mobile.
- Các trang chính:
  - Trang chủ.
  - Trang chuyên mục.
  - Trang chi tiết bài viết.
  - Thanh tìm kiếm thông minh, phản hồi dưới 200ms.

---

### 2.5. Phân hệ Lập lịch tự động

- Chạy nền định kỳ quét trang 1–2 để cập nhật tin mới hàng giờ.
- Với dữ liệu lịch sử, chạy batch quét từ trang 1 đến 20.
- Tần suất đề xuất: mỗi 15–30 phút cho tin mới.

---

## 3. Tech Stack đề xuất

| Phân hệ | Công nghệ đề xuất | Lý do |
| --- | --- | --- |
| Crawler | Python (Scrapy hoặc HTTPX + BeautifulSoup, Playwright khi cần) | Hệ sinh thái scraper trưởng thành, xử lý bất đồng bộ tốt, dễ parse HTML/RSS. |
| Task Queue | Redis + Celery hoặc RQ | Tách biệt crawl URL và crawl chi tiết, tránh nghẽn, dễ scale. |
| Backend API | FastAPI (Python) hoặc Go (Gin/Fiber) | FastAPI đồng bộ hệ sinh thái Python, async nhanh, tự sinh OpenAPI. Go phù hợp nếu cần hiệu năng I/O cao. |
| Database | PostgreSQL + `pg_trgm` + Full-Text Search | Quan hệ tốt, hỗ trợ tìm kiếm tiếng Việt, JSONB linh hoạt. |
| Search mở rộng | Meilisearch hoặc Elasticsearch | Tìm kiếm nhanh, typo-tolerant khi dữ liệu lớn. |
| Frontend | Next.js (React) + Tailwind CSS | SSR tối ưu tốc độ đọc báo, dễ tùy biến giao diện. |
| Hạ tầng | Docker, Docker Compose | Đóng gói đồng nhất Crawler, DB, Backend, Frontend trên VPS cá nhân. |

---

## 4. Thiết kế cơ sở dữ liệu mẫu

```sql
-- Bảng danh mục hỗ trợ đa tầng (cha - con)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    parent_id INT REFERENCES categories(id) ON DELETE CASCADE,
    origin_url VARCHAR(500) NOT NULL
);

-- Bảng bài viết
CREATE TABLE articles (
    id BIGINT PRIMARY KEY, -- ID bài báo VnExpress, ví dụ: 5121093
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL,
    description TEXT,
    content_html TEXT NOT NULL,
    content_text TEXT NOT NULL,
    thumbnail_url VARCHAR(500),
    origin_url VARCHAR(500) UNIQUE NOT NULL,
    category_id INT REFERENCES categories(id),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chỉ mục hỗ trợ tìm kiếm nhanh
CREATE INDEX idx_articles_search
ON articles
USING gin(to_tsvector('simple', title || ' ' || content_text));

CREATE INDEX idx_articles_category
ON articles(category_id, published_at DESC);
```

Có thể bổ sung bảng `media`, `tags`, `article_tags`, `crawl_logs` để quản lý media, tagging và log tiến trình cào.

---

## 5. Kiến trúc tổng thể

Luồng hoạt động đề xuất:

1. **Scheduler** kích hoạt crawler theo lịch.
2. **Crawler** quét RSS/danh mục, thu thập URL bài viết.
3. **Redis Set** lọc trùng theo `article_id`.
4. **Task Queue** đẩy URL mới vào worker để crawl chi tiết.
5. **Parser** trích xuất metadata, nội dung, media.
6. **PostgreSQL** lưu bài viết, danh mục, media, log.
7. **Search Index** cập nhật chỉ mục tìm kiếm.
8. **Backend API** phục vụ Frontend.
9. **Frontend Next.js** hiển thị giao diện đọc báo.

---

## 6. Lộ trình triển khai

### Giai đoạn 1: Khảo sát & Xây dựng Crawler Core (1–2 ngày)

- Phân tích cấu trúc DOM và RSS feed của VnExpress.
- Viết parser bóc tách nội dung chi tiết: bài text, photo story, video.
- Crawl toàn bộ danh mục cha và con, lưu vào bảng `categories`.
- Duyệt trang 1–20, trích xuất link dạng `.*-(\d+)\.html`.
- Đẩy `article_id` vào Redis Set để lọc trùng.
- Cấu hình `DOWNLOAD_DELAY = 0.5–1s`, rotating User-Agent, retry.
- Kiểm thử độ chính xác dữ liệu và cơ chế chống trùng.

### Giai đoạn 2: Thiết kế Schema & Backend Core (1–2 ngày)

- Thiết kế ERD database: Articles, Categories, Media, Crawl_Logs.
- Dựng REST API cơ bản: CRUD, Pagination, Category filtering.
- Thiết lập Full-Text Search trên PostgreSQL.
- API danh mục, danh sách bài viết, chi tiết bài viết, tìm kiếm.

### Giai đoạn 3: Phát triển Frontend News Reader (2–3 ngày)

- Xây dựng header menu điều hướng đa cấp.
- Layout trang danh sách bài viết: thumbnail, sapo, thời gian đăng.
- Trang đọc bài viết tối ưu typography, căn chỉnh hình ảnh.
- Loại bỏ quảng cáo, tracker từ trang gốc.
- Tích hợp thanh tìm kiếm thông minh, phản hồi dưới 200ms.
- Hỗ trợ Dark/Light mode và responsive.

### Giai đoạn 4: Tự động hóa & Triển khai (1 ngày)

- Cấu hình Docker Compose cho toàn bộ hệ thống.
- Thiết lập Task Scheduler/Cron job cào bài mới mỗi 15–30 phút.
- Cấu hình health check, logging, giám sát crawler.
- Triển khai trên VPS cá nhân hoặc môi trường cloud.

---

## 7. Triển khai & Vận hành

- Đóng gói toàn bộ dịch vụ bằng Docker Compose:
  - Crawler/Worker
  - Redis
  - PostgreSQL
  - Backend API
  - Frontend
- Thiết lập cron job hoặc Celery Beat để cào tin mới.
- Ghi log crawl, theo dõi lỗi request, tỷ lệ thành công.
- Có cơ chế retry và cảnh báo khi crawler bị chặn hoặc lỗi kéo dài.

---

## 8. Lưu ý về lưu trữ media

Cần quyết định phương án lưu trữ hình ảnh:

- **Phương án 1:** Chỉ lưu URL ảnh trực tiếp từ VnExpress. Ưu điểm: đơn giản, nhẹ hệ thống. Nhược điểm: phụ thuộc link gốc, có thể bị hỏng hoặc hotlink protection.
- **Phương án 2:** Tải toàn bộ hình ảnh về ổ cứng/S3 riêng. Ưu điểm: chủ động dữ liệu, tránh link hỏng. Nhược điểm: tốn dung lượng, cần quản lý media.

Khuyến nghị: nếu mục tiêu là lưu trữ lâu dài và đọc ngoại tuyến, nên tải media về S3/ổ cứng. Nếu chỉ cần hiển thị trực tuyến, có thể lưu URL gốc để giảm tải.

---

## 9. Kết luận

Dự án News Aggregator từ VnExpress có tính khả thi cao, phù hợp để triển khai trên VPS cá nhân với Docker Compose. Kiến trúc đề xuất gồm Python Crawler, Redis + Celery, PostgreSQL, Backend FastAPI/Go, Frontend Next.js. Hệ thống có thể tự động cập nhật tin mới, lưu trữ lâu dài, tìm kiếm nhanh và mang lại trải nghiệm đọc báo tối giản, hiệu quả.