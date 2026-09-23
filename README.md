# VnExpress News Aggregator & Telemetry Reader

> Hệ thống tự động thu thập, khử trùng lặp, lưu trữ và cung cấp giao diện đọc báo VnExpress tối giản, tốc độ cao theo phong cách **Tactical Telemetry Brutalist** (màu nền Cyberpunk đen tối giản, điểm nhấn đỏ neon `#E61919`, font monospace, lược bỏ hoàn toàn quảng cáo và theo dõi người dùng).

---

## Mục Lục
1. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
2. [Cấu Trúc Trang & Quy Tắc Phân Trang VnExpress](#cấu-trúc-trang--quy-tắc-phân-trang-vnexpress)
3. [Cơ Chế Bóc Tách Lượt Bình Luận (Comment Extraction)](#cơ-chế-bóc-tách-lượt-bình-luận-comment-extraction)
4. [Khử Trùng Lặp Thông Minh (Deduplication)](#khử-trùng-lặp-thông-minh-deduplication)
5. [Cài Đặt & Khởi Chạy](#cài-đặt--khởi-chạy)
6. [Bộ Lệnh CLI Hoàn Chỉnh](#bộ-lệnh-cli-hoàn-chỉnh)
7. [Bộ Lệnh Minh Họa Cào Đủ Cho "Khoa Học Công Nghệ"](#bộ-lệnh-minh-họa-cào-đủ-cho-khoa-học-công-nghệ)
8. [Hệ Thống Cronjob Phân Bổ Hằng Tuần & Script Cronjob.sh (122 Danh Mục)](#hệ-thống-cronjob-phân-bổ-hằng-tuần--script-cronjobsh-122-danh-mục)
9. [Cấu Hình & Sử Dụng Proxy Chống Chặn IP (HTTP / HTTPS / SOCKS5)](#cấu-hình--sử-dụng-proxy-chống-chặn-ip-http--https--socks5)
10. [Chiến Lược Cào Tin Khuyến Nghị (Best Practices)](#chiến-lược-cào-tin-khuyến-nghị-best-practices)
11. [Bộ Lọc & Tìm Kiếm Tiếng Việt Có Dấu / Không Dấu](#bộ-lọc--tìm-kiếm-tiếng-việt-có-dấu--không-dấu)
12. [Kiểm Thử (Testing) & Khôi Phục Dữ Liệu](#kiểm-thử-testing--khôi-phục-dữ-liệu)

---

## Kiến Trúc Hệ Thống

```mermaid
flowchart TD
    subgraph VnExpress ["VnExpress Network"]
        VNE_Home["VnExpress Homepage & RSS"]
        VNE_Cat["Category Stream (p1 -> p20)"]
        VNE_Detail["Article Detail (*-<id>.html)"]
        VNE_CommentAPI["SaaS Comment API (usi-saas.vnexpress.net)"]
    end

    subgraph CrawlerCore ["Crawler Core (Python / BeautifulSoup4 / HTTPX)"]
        HttpClient["HttpClient (User-Agent Rotation & Exponential Backoff)"]
        Parsers["Parsers (Category, Listing, Article, RSS)"]
        Deduplicator["Deduplicator (Local In-Memory Set / Redis)"]
        Pipeline["Article & Category Sync Pipeline"]
    end

    subgraph StorageLayer ["Storage & Database (SQLite / SQLAlchemy)"]
        DB[(news.db)]
        SQLite_Accents["Custom SQLite Function (remove_accents)"]
    end

    subgraph BackendCore ["Backend API (FastAPI / Uvicorn)"]
        API_Articles["/api/v1/articles (List, Detail, Hot Sort)"]
        API_Categories["/api/v1/categories (Tree, Flat)"]
        API_Search["/api/v1/search (Exact Accent & Full Unaccented)"]
        API_Crawler["/api/v1/crawler (Health Check, Background Tasks)"]
    end

    subgraph FrontendUI ["Frontend UI (Next.js 14 App Router / Tailwind CSS)"]
        UI_Header["Tactical Header (Dual-row Topic Navigation)"]
        UI_Home["Home Dashboard (Featured Hero, Category Blocks, Hot News)"]
        UI_Reader["Reader View (Clean Typography, Media Galleries, Comment Telemetry)"]
        UI_Crawler["Admin Dashboard (/crawler - Health Monitor & Trigger)"]
    end

    VNE_Home --> HttpClient
    VNE_Cat --> HttpClient
    VNE_Detail --> HttpClient
    VNE_CommentAPI --> HttpClient

    HttpClient --> Parsers
    Parsers --> Deduplicator
    Deduplicator --> Pipeline
    Pipeline --> DB
    DB --- SQLite_Accents

    DB --> BackendCore
    BackendCore --> FrontendUI
```

---

## Cấu Trúc Trang & Quy Tắc Phân Trang VnExpress

VnExpress tổ chức bài viết theo cấu trúc phân tầng:

### 1. Chuyên mục cha & các chủ đề con (Subtopics)
Ví dụ với chuyên mục **Khoa học Công nghệ** (`/khoa-hoc-cong-nghe`):
- **Trang chủ chuyên mục**: `https://vnexpress.net/khoa-hoc-cong-nghe`
- **Các chủ đề con (Subtopics)**:
  - Hoạt động Bộ KH&CN: `https://vnexpress.net/khoa-hoc-cong-nghe/bo-khoa-hoc-va-cong-nghe`
  - Chuyển đổi số: `https://vnexpress.net/khoa-hoc-cong-nghe/chuyen-doi-so`
  - Đổi mới sáng tạo: `https://vnexpress.net/khoa-hoc-cong-nghe/doi-moi-sang-tao`
  - Trí tuệ nhân tạo (AI): `https://vnexpress.net/khoa-hoc-cong-nghe/ai`
  - Vũ trụ: `https://vnexpress.net/khoa-hoc-cong-nghe/vu-tru`
  - Thế giới tự nhiên: `https://vnexpress.net/khoa-hoc-cong-nghe/the-gioi-tu-nhien`
  - Thiết bị: `https://vnexpress.net/khoa-hoc-cong-nghe/thiet-bi`
  - AI4VN: `https://vnexpress.net/khoa-hoc-cong-nghe/ai4vn-2026`
  - Tech Awards: `https://vnexpress.net/khoa-hoc-cong-nghe/tech-awards`
  - Sáng kiến khoa học: `https://vnexpress.net/khoa-hoc-cong-nghe/cuoc-thi-sang-kien-khoa-hoc`

### 2. Quy tắc phân trang (1 đến 20 trang)
- **Trang 1**: Có cấu trúc đa container (`wrapper-topstory-folder`, `news-container01` đến `04`), chứa bài tiêu điểm và luồng tin mới nhất.
- **Trang 2 đến 20**: Tuân theo quy tắc gắn hậu tố `-p{trang}`:
  - Trang 2: `https://vnexpress.net/khoa-hoc-cong-nghe-p2`
  - Trang 3: `https://vnexpress.net/khoa-hoc-cong-nghe-p3`
  - ...
  - Trang 20: `https://vnexpress.net/khoa-hoc-cong-nghe-p20`
- **Chủ đề con cũng có 20 trang tương tự**:
  - `https://vnexpress.net/khoa-hoc-cong-nghe/ai-p2` ... `ai-p20`
  - `https://vnexpress.net/khoa-hoc-cong-nghe/thiet-bi-p2` ... `thiet-bi-p20`

### 3. Cấu trúc URL bài viết đơn lẻ
Mọi bài báo trên VnExpress đều kết thúc bằng mã ID số nguyên duy nhất:
- `https://vnexpress.net/video-ngan-tu-youtuber-viet-tang-hon-100-sau-mot-nam-5121093.html` (ID: `5121093`)
- `https://vnexpress.net/canon-eos-r8-mark-ii-may-anh-full-frame-gia-45-trieu-dong-5121082.html` (ID: `5121082`)
- Bài tổng thuật: `...-5121155-tong-thuat.html` (ID: `5121155`)

---

## Cơ Chế Bóc Tách Lượt Bình Luận (Comment Extraction)

Hệ thống không sử dụng dữ liệu giả lập (mock data) mà trích xuất chính xác theo 3 tầng bảo đảm:

1. **Trích xuất từ HTML chi tiết bài viết ([article.py](crawler/parsers/article.py))**:
   - Bóc tách từ thẻ: `<label id="total_comment">26</label>`, `#total_comment`, `.ykien_vne #total_comment`, `.ykien_vne label`.
   - Bóc tách từ thẻ widget: `<span class="number_cmt num_cmt_detail widget-comment-{id}-1">3</span>`.
2. **Trích xuất từ HTML danh sách ([listing.py](crawler/parsers/listing.py))**:
   - Bóc tách từ thẻ: `.meta-news .count_cmt span`, `.count_cmt [class*="widget-comment-"]`, `.meta-news .font_icon`.
   - Ví dụ: `<span class="font_icon widget-comment-5122309-1">21</span>` trích xuất chính xác số `21`.
3. **Đồng bộ thời gian thực qua VnExpress SaaS Comment API ([article_pipeline.py](crawler/pipeline/article_pipeline.py))**:
   - Khi cào tin trực tiếp mà HTML tĩnh không kèm sẵn số bình luận (do VnExpress render bằng JavaScript phía trình duyệt), hệ thống tự động gọi API:
     ```
     https://usi-saas.vnexpress.net/index/get?objectid={id}&objecttype=1&siteid=1000000
     ```
   - Trường `data.total` trong JSON trả về sẽ cung cấp số lượt bình luận thực tế chính xác 100%.
4. **Lệnh làm mới lượt bình luận**:
   - Có thể chạy lệnh `update-comments` bất kỳ lúc nào để làm mới số comment cho các bài viết đã có trong DB.

---

## Khử Trùng Lặp Thông Minh (Deduplication)

- **Cơ chế**: Dựa trên ID bài viết (`article_id`).
- **Chế độ In-Memory (Mặc định)**: Khi khởi động, nạp toàn bộ danh sách ID đã lưu từ SQLite vào `Set[int]`. Các thao tác kiểm tra tồn tại `is_seen(id)` đạt độ phức tạp $O(1)$.
- **Chế độ Redis**: Tự động chuyển đổi sang Redis Set (`SADD`, `SISMEMBER`) khi cấu hình `REDIS_URL`.
- **Độ tin cậy**: Khi duyệt qua hàng chục trang và các chuyên mục con, nếu bài viết đã xuất hiện ở chuyên mục cha, bộ lọc sẽ bỏ qua ngay lập tức, không gửi request tải lại chi tiết, tiết kiệm 80-90% băng thông và thời gian.

---

## Cài Đặt & Khởi Chạy

### 1. Chuẩn bị môi trường
Yêu cầu:
- Python 3.10 trở lên (khuyến nghị Python 3.12 hoặc 3.13)
- Node.js 18 trở lên & npm

### 2. Cài đặt Backend
```bash
# Tạo môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cài đặt Frontend
```bash
cd frontend
npm install
cd ..
```

### 4. Khởi chạy hệ thống

**Khởi chạy Backend (Port 8000):**
```bash
./.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/crawler/health`

**Khởi chạy Frontend (Port 3000):**
```bash
cd frontend
npm run dev
```
- Website: `http://localhost:3000`
- Dashboard Quản trị Crawler: `http://localhost:3000/crawler`

---

## Bộ Lệnh CLI Hoàn Chỉnh

Hệ thống cung cấp CLI thông qua module `crawler.cli`:

| Lệnh CLI | Mô tả chi tiết |
| :--- | :--- |
| `init-db` | Khởi tạo cấu trúc bảng cơ sở dữ liệu SQLite (`news.db`). |
| `sync-categories` | Thu thập và đồng bộ toàn bộ cây danh mục cha và danh mục con từ VnExpress. |
| `list-categories` | In ra toàn bộ cây danh mục hiện có trong cơ sở dữ liệu. |
| `crawl-category <slug> [--pages N] [-r] [--proxy URL]` | Cào tin từ chuyên mục (hỗ trợ phân trang, đệ quy mục con `-r`, và Proxy). |
| `crawl-rss [--topic <name>] [--max-articles N] [--proxy URL]` | Cào tin nhanh nhất từ luồng RSS của VnExpress qua Proxy. |
| `crawl-article <url> [--proxy URL]` | Cào chi tiết một bài viết cụ thể qua URL. |
| `update-comments [--limit N] [--proxy URL]` | Đồng bộ số lượt bình luận trực tiếp từ VnExpress SaaS Comment API. |
| `cron-run [--mode M] [--day D] [--slot S] [--proxy URL]` | Thực thi lịch cào định kỳ phân bổ theo ngày/khung giờ. |
| `stats` | Hiển thị bảng thống kê tổng quan (danh mục, bài viết, media, log cào gần nhất). |
| *Tùy chọn chung:* `--proxy, -p <url>` | Định tuyến toàn bộ kết nối qua HTTP/HTTPS hoặc SOCKS5 Proxy. |
| *Tùy chọn chung:* `-v, --verbose` | Bật chế độ ghi nhật ký chi tiết (DEBUG). |

---

## Bộ Lệnh Minh Họa Cào Đủ Cho "Khoa Học Công Nghệ"

### Tình huống: Hiện chưa có tin nào trong DB, muốn cào đầy đủ thì làm thế nào?

Khi chưa có dữ liệu nào, bạn thực hiện theo 3 bước sau:

#### Bước 1: Khởi tạo database và đồng bộ cây chuyên mục con
```bash
# 1. Khởi tạo bảng dữ liệu
./.venv/bin/python -m crawler.cli init-db

# 2. Đồng bộ danh mục để nạp đủ các mục con (AI, Thiết bị, Đổi mới sáng tạo, v.v.)
./.venv/bin/python -m crawler.cli sync-categories

# 3. Kiểm tra các mục con đã có trong DB
./.venv/bin/python -m crawler.cli list-categories
```

---

#### Cách A: Cào 1 Lệnh Duy Nhất (Đệ quy danh mục cha + toàn bộ 10 mục con)
Sử dụng cờ `-r` / `--recursive` đã được tích hợp sẵn:
```bash
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe --pages 20 --recursive
```
*Lệnh này sẽ tự động duyệt qua:*
1. `khoa-hoc-cong-nghe` (Trang 1 đến 20)
2. `khoa-hoc-cong-nghe/bo-khoa-hoc-va-cong-nghe` (Trang 1 đến 20)
3. `khoa-hoc-cong-nghe/chuyen-doi-so` (Trang 1 đến 20)
4. `khoa-hoc-cong-nghe/doi-moi-sang-tao` (Trang 1 đến 20)
5. `khoa-hoc-cong-nghe/ai` (Trang 1 đến 20)
6. `khoa-hoc-cong-nghe/vu-tru` (Trang 1 đến 20)
7. `khoa-hoc-cong-nghe/the-gioi-tu-nhien` (Trang 1 đến 20)
8. `khoa-hoc-cong-nghe/thiet-bi` (Trang 1 đến 20)
9. `khoa-hoc-cong-nghe/ai4vn-2026` (Trang 1 đến 20)
10. `khoa-hoc-cong-nghe/tech-awards` (Trang 1 đến 20)
11. `khoa-hoc-cong-nghe/cuoc-thi-sang-kien-khoa-hoc` (Trang 1 đến 20)
*Mỗi khi gặp bài viết trùng lặp giữa mục cha và mục con, deduplicator sẽ tự động bỏ qua trong 0.1ms.*

---

#### Cách B: Bộ Lệnh Thủ Công Theo Từng Chủ Đề Trọng Tâm
Nếu muốn kiểm soát tốc độ hoặc ưu tiên cào các chủ đề "hot" trước:

```bash
# 1. Cào 20 trang mục chính Khoa học Công nghệ (khoảng 300 - 400 bài)
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe --pages 20

# 2. Cào 20 trang chủ đề Trí tuệ nhân tạo (AI)
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/ai --pages 20

# 3. Cào 20 trang chủ đề Thiết bị công nghệ (Smartphone, Laptop, Audio, Camera)
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/thiet-bi --pages 20

# 4. Cào 20 trang chủ đề Chuyển đổi số
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/chuyen-doi-so --pages 20

# 5. Cào 20 trang chủ đề Vũ trụ & Khoa học khám phá
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/vu-tru --pages 20

# 6. Cào 20 trang chủ đề Thế giới tự nhiên
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/the-gioi-tu-nhien --pages 20

# 7. Cào 20 trang chủ đề Đổi mới sáng tạo
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/doi-moi-sang-tao --pages 20

# 8. Cào 20 trang chủ đề Hoạt động Bộ KH&CN
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/bo-khoa-hoc-va-cong-nghe --pages 20

# 9. Cào 20 trang sự kiện AI4VN & Tech Awards
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/ai4vn-2026 --pages 20
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/tech-awards --pages 20
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe/cuoc-thi-sang-kien-khoa-hoc --pages 20
```

---

#### Bước 3: Đồng bộ số lượng bình luận mới nhất & xem thống kê
```bash
# Đồng bộ số lượt bình luận trực tiếp cho 100 bài viết mới nhất
./.venv/bin/python -m crawler.cli update-comments --limit 100

# Xem thống kê tổng số lượng bài viết và media đã thu thập
./.venv/bin/python -m crawler.cli stats
```

---

## Hệ Thống Cronjob Phân Bổ Hằng Tuần & Script Cronjob.sh (122 Danh Mục)

Hệ thống cung cấp giải pháp cào tin định kỳ tự động hóa 100%, bảo đảm lấy đủ:
- **100 bài mới nhất toàn trang** (Breaking News qua RSS tổng hợp).
- **100 bài mới nhất ở mỗi mục cha (17 mục)** và **100 bài mới nhất của từng mục con (105 mục con)** $\rightarrow$ **Tổng cộng 122 danh mục**.
- **Chia đều các khung giờ trong ngày** (sáng sớm 02:00, trưa 13:00, tối 20:00) nhằm giảm tải, không gây nghẽn băng thông và loại trừ rủi ro bị chặn IP.

### 1. Bảng Phân Bổ 122 Danh Mục & Các Khung Giờ Trong Tuần

| Thứ | Khung Giờ | Cụm Chuyên Mục | Chi Tiết Danh Mục | Số Danh Mục |
| :--- | :---: | :--- | :--- | :---: |
| **Thứ 2** | `02:00` (Slot 1)<br>`13:00` (Slot 2) | Thời sự & Quốc tế | • `thoi-su` (1 cha + 6 con: Chính trị, Dân sinh, Lao động, Giao thông...)<br>• `the-gioi` (1 cha + 6 con: Tư liệu, Phân tích, Người Việt năm châu...) | **14** |
| **Thứ 3** | `02:00` (Slot 1)<br>`13:00` (Slot 2) | Kinh tế & Bất động sản | • `kinh-doanh` (1 cha + 9 con: Quốc tế, Doanh nghiệp, Chứng khoán, Ebank...)<br>• `bat-dong-san` (1 cha + 6 con: Chính sách, Thị trường, Dự án...) | **17** |
| **Thứ 4** | `02:00` (Slot 1)<br>`13:00` (Slot 2) | Khoa học Công nghệ & Xe | • `khoa-hoc-cong-nghe` (1 cha + 10 con: Chuyển đổi số, AI, Thiết bị...)<br>• `oto-xe-may` (1 cha + 8 con: Thị trường, Xe điện, Diễn đàn...) | **20** |
| **Thứ 5** | `02:00` (Slot 1)<br>`13:00` (Slot 2)<br>`20:00` (Slot 3) | Thể thao, Giải trí & Thư giãn | • `the-thao` (1 cha + 8 con: Bóng đá, Tennis, Marathon...)<br>• `giai-tri` (1 cha + 8 con: Giới sao, Phim, Nhạc, Thời trang...)<br>• `thu-gian` (1 cha + 6 con: Cười, Đố vui, Chuyện lạ...) | **25** |
| **Thứ 6** | `02:00` (Slot 1)<br>`13:00` (Slot 2)<br>`20:00` (Slot 3) | Sức khỏe, Đời sống & Du lịch | • `suc-khoe` (1 cha + 5 con: Tin tức, Dinh dưỡng, Khỏe đẹp...)<br>• `doi-song` (1 cha + 5 con: Tổ ấm, Bài học sống, Nhà...)<br>• `du-lich` (1 cha + 7 con: Điểm đến, Ẩm thực, Dấu chân...) | **20** |
| **Thứ 7** | `02:00` (Slot 1)<br>`13:00` (Slot 2)<br>`20:00` (Slot 3) | Giáo dục, Pháp luật, Xã hội | • `giao-duc` (1 cha + 8 con: Tuyển sinh, Du học, Học tiếng Anh...)<br>• `phap-luat` + `goc-nhin` (2 cha + 10 con: Hồ sơ vụ án, Bình luận...)<br>• `y-kien` + `tam-su` (2 cha + 3 con: Đời sống, Góc nhìn...) | **26** |
| **Chủ nhật**| `03:00` (Slot 1)<br>`14:00` (Slot 2) | Bảo trì & Tối ưu hóa | • Đồng bộ lượt bình luận thời gian thực cho 500 bài viết mới nhất<br>• Tối ưu hóa Database (`SQLite VACUUM & ANALYZE`) | *Bảo trì* |
| **TẤT CẢ** | `00` phút mỗi giờ | **100 tin mới nhất (RSS)** | Quét liên tục 13 kênh RSS chính để cập nhật tin nóng tức thì | **24/7** |

---

### 2. Quản Trị Trực Tiếp Qua File `Cronjob.sh`

Tất cả tác vụ và lịch trình đã được tích hợp trọn vẹn trong một tệp duy nhất: `./Cronjob.sh`.

#### Cú pháp các lệnh:

```bash
# 1. Xem bảng lịch trình phân bổ 122 danh mục
./Cronjob.sh schedule

# 2. Cào ngay 100 tin mới nhất toàn trang (Breaking RSS)
./Cronjob.sh hourly

# 3. Kích hoạt cào danh mục theo ngày hiện tại hoặc chỉ định ngày/khung giờ
./Cronjob.sh daily today               # Chạy toàn bộ các slot của ngày hôm nay
./Cronjob.sh daily mon slot1           # Chạy Slot 1 Thứ 2 (Thời sự: 1 cha + 6 con)
./Cronjob.sh daily wed slot2           # Chạy Slot 2 Thứ 4 (Xe: 1 cha + 8 con)

# 4. Chạy bảo trì (Đồng bộ bình luận và tối ưu database)
./Cronjob.sh maintenance

# 5. Chạy tuần tự toàn bộ 122 danh mục trong hệ thống
./Cronjob.sh all

# 6. Xem thống kê dữ liệu hiện tại
./Cronjob.sh status
```

---

### 3. Cài Đặt Crontab Tự Động Lên Hệ Điều Hành (Linux / macOS)

Chỉ với một lệnh duy nhất, `./Cronjob.sh` sẽ tự động cấu hình lịch trình chạy ngầm vào crontab hệ điều hành của bạn:

```bash
# Cài đặt tự động vào crontab:
./Cronjob.sh install

# Kiểm tra crontab đã cài đặt:
crontab -l

# Xem nội dung cấu hình crontab mẫu:
./Cronjob.sh crontab-show

# Gỡ bỏ lịch trình khi không còn nhu cầu:
./Cronjob.sh uninstall
```

Logs thực thi được tự động lưu lại tại thư mục `data/logs/`:
- `data/logs/cron_hourly.log`: Log cào 100 tin mới mỗi giờ.
- `data/logs/cron_daily.log`: Log cào danh mục theo khung giờ hàng ngày.
- `data/logs/cron_maint.log`: Log bảo trì và tối ưu database Chủ nhật.

---

## Cấu Hình & Sử Dụng Proxy Chống Chặn IP (HTTP / HTTPS / SOCKS5)

Hệ thống hỗ trợ toàn diện các giao thức Proxy (**HTTP, HTTPS, SOCKS5**) cho cả **quy trình thủ công** (CLI cào từng bài, từng mục) lẫn **quy trình tự động** (Cronjob theo tuần, Cronjob.sh, FastAPI Background Tasks).

### 1. Các giải pháp Proxy khuyến nghị

| Giải pháp | Giao thức & Cấu hình mẫu | Ưu điểm & Ứng dụng |
| :--- | :--- | :--- |
| **Cloudflare WARP** | `socks5://127.0.0.1:40000` | **Khuyên dùng nhất**: Miễn phí 100%, IP Cloudflare sạch, tốc độ cao, không bị chặn rate-limit. |
| **Tor Proxy** | `socks5://127.0.0.1:9050` | Đổi IP linh hoạt bằng `systemctl reload tor`. Miễn phí nhưng tốc độ có thể chậm hơn. |
| **Residential Rotating Proxy** | `http://user:pass@proxy.provider.com:8080` | Xoay vòng IP người dùng dân cư tự động sau mỗi request, thích hợp cho quy mô lớn. |
| **4G/5G USB Tethering** | *Không cần cấu hình trong code* | Cắm cáp điện thoại vào PC, bật USB Tethering. Bật/tắt Airplane mode để đổi IP ngay lập tức. |

> [!NOTE]
> Môi trường ảo của dự án đã cài đặt sẵn thư viện `socksio>=1.0.0` để hỗ trợ giao thức `socks5://` mượt mà với `httpx`.

---

### 2. Sử dụng Proxy trong lệnh thủ công (CLI)

Bạn có thể truyền cờ `--proxy` (hoặc `-p`) vào bất kỳ lệnh cào dữ liệu nào:

```bash
# 1. Cào một chuyên mục qua Cloudflare WARP (SOCKS5):
./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe --pages 5 --proxy "socks5://127.0.0.1:40000"

# 2. Cào bài viết đơn lẻ qua HTTP Proxy có mật khẩu:
./.venv/bin/python -m crawler.cli crawl-article "https://vnexpress.net/..." --proxy "http://username:password@ip_proxy:port"

# 3. Cào RSS tin nóng qua Tor Proxy:
./.venv/bin/python -m crawler.cli crawl-rss --topic tin-moi-nhat --proxy "socks5://127.0.0.1:9050"

# 4. Chạy lịch trình định kỳ có kèm Proxy:
./.venv/bin/python -m crawler.cli cron-run --mode daily --day wed --slot slot1 --proxy "socks5://127.0.0.1:40000"
```
*(Lưu ý: Mật khẩu trong URL Proxy sẽ được tự động làm mờ (`***`) khi ghi vào log để đảm bảo an toàn bảo mật).*

---

### 3. Cấu hình tự động cho Cronjob & Backend

#### Cách 1: Thiết lập qua file `.env`
Khai báo biến `PROXY_URL` trong file `.env` ở thư mục gốc:
```env
PROXY_URL=socks5://127.0.0.1:40000
# Hoặc:
# PROXY_URL=http://username:password@ip_proxy:port
```
Khi đó, toàn bộ tác vụ nền (FastAPI Backend, Background Tasks, Cronjob) sẽ tự động nạp cấu hình Proxy này.

#### Cách 2: Thiết lập qua biến môi trường khi chạy `Cronjob.sh`
```bash
# Chạy cào tin mỗi giờ qua Proxy:
PROXY_URL="socks5://127.0.0.1:40000" ./Cronjob.sh hourly

# Chạy cào danh mục hôm nay qua Proxy:
PROXY_URL="socks5://127.0.0.1:40000" ./Cronjob.sh daily today

# Chạy bảo trì database & đồng bộ comment qua Proxy:
PROXY_URL="socks5://127.0.0.1:40000" ./Cronjob.sh maintenance
```
Khi cấu hình trong Crontab hệ điều hành (`./Cronjob.sh install`), script sẽ tự động kiểm tra `PROXY_URL` trong `.env` để bảo đảm các tiến trình chạy ngầm ban đêm đều đi qua Proxy sạch.

---

## 10. Chiến Lược Cào Tin Khuyến Nghị (Best Practices)

### Có nên cào hết vài nghìn tin ngay lập tức không?
> **Khuyến nghị: KHÔNG NÊN cào dồn dập hàng nghìn bài trong một lần chạy duy nhất.**

**Lý do:**
1. **Tránh bị tường lửa VnExpress khóa IP tạm thời**: Mặc dù crawler đã tích hợp xoay vòng User-Agent và độ trễ ngẫu nhiên (`download_delay: 0.5s - 1.0s`), việc gửi liên tục 2.000 - 3.000 requests trong thời gian ngắn có thể kích hoạt cơ chế chống DDoS / rate-limit của CDN (VnExpress CDN / Akamai).
2. **Nhu cầu sử dụng thực tế**: Người dùng chủ yếu đọc tin tức trong khoảng 1-2 tuần gần nhất. 100 - 200 bài viết là quá đủ để lấp đầy giao diện trang chủ, các trang chuyên mục, tin hot và thanh tìm kiếm.

### Quy trình cào tin chuẩn (Staged Crawling):
- **Giai đoạn 1 (Khởi tạo nhanh - 1 phút)**:
  Cào RSS `tin-moi-nhat` (30 bài) + 2 trang đầu của các mục lớn (`khoa-hoc-cong-nghe --pages 2`, `thoi-su --pages 2`). Website có ngay ~100 bài viết để trải nghiệm toàn bộ tính năng.
- **Giai đoạn 2 (Cào sâu theo nhu cầu)**:
  Cào 5 đến 10 trang của các mục chuyên sâu bạn quan tâm.
- **Giai đoạn 3 (Duy trì định kỳ)**:
  Kích hoạt cào RSS hoặc cào 1 trang danh mục mỗi 15-30 phút để luôn có bài mới nhất mà không gây nghẽn mạng.

---

## 11. Bộ Lọc & Tìm Kiếm Tiếng Việt Có Dấu / Không Dấu

Hệ thống xây dựng giải pháp tìm kiếm toàn diện cho tiếng Việt trên SQLite:

1. **Tìm kiếm không dấu (Accent-Insensitive)**:
   - Tự động chuẩn hóa unicode (NFD -> strip diacritics -> NFC) bằng hàm C-Extension / Python `remove_accents` đăng ký trực tiếp vào SQLite Engine.
   - Tìm `"ha noi"` sẽ tìm thấy cả `"Hà Nội"`, `"hà nội"`, `"HA NOI"`.
2. **Tìm kiếm có dấu chính xác (Accent-Sensitive Precision)**:
   - Sử dụng regex word-boundary tiếng Việt `(?i)(?:^|[\s,.\-—:;!?()\[\]"'/])<query>(?:$|[\s,.\-—:;!?()\[\]"'/])`.
   - Tìm `"Vinh"` (thành phố Vinh) sẽ **không** bị khớp nhầm vào chữ `"vinh"` trong `"vinh danh"` hay `"vinh quang"`.
3. **Lọc bài viết HOT theo lượt bình luận**:
   - Query parameter `sort=hot` & `min_comments=10`.
   - Giao diện gắn huy hiệu `HOT // {N} CMT` màu đỏ neon rực rỡ kèm hiệu ứng pulsing.

---

## 12. Kiểm Thử (Testing) & Khôi Phục Dữ Liệu

### 1. Chạy toàn bộ Test Suite
```bash
./.venv/bin/pytest tests/ -v
```
Toàn bộ **58 tests** (API, Parser, Storage, Deduplicator, Search, Proxy Support) đều được tự động hóa.

### 2. Khôi phục dữ liệu nếu lỡ xóa file DB (`news.db`)
Việc xóa file `news.db` **hoàn toàn an toàn và khôi phục cực kỳ dễ dàng**:
1. Khởi động lại uvicorn (hoặc chạy bất kỳ lệnh CLI nào), database và các bảng sẽ tự động được tạo mới 100%.
2. Chạy lệnh:
   ```bash
   ./.venv/bin/python -m crawler.cli sync-categories
   ./.venv/bin/python -m crawler.cli crawl-rss --topic tin-moi-nhat --max-articles 30
   ./.venv/bin/python -m crawler.cli crawl-category khoa-hoc-cong-nghe --pages 2
   ```
   Chỉ trong 30 giây, cơ sở dữ liệu đã sẵn sàng hoạt động trở lại!

---

## Giấy Phép & Bản Quyền
Dự án được xây dựng cho mục đích nghiên cứu, học tập và trải nghiệm đọc tin tối giản không quảng cáo. Toàn bộ bản quyền bài viết và hình ảnh thuộc về [Báo điện tử VnExpress](https://vnexpress.net).

