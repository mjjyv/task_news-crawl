#!/usr/bin/env bash
# ==============================================================================
# Cronjob.sh - Quản Lý & Thực Thi Cronjob Cào Tin VnExpress Tự Động
# Hệ thống phân bổ 122 danh mục (17 cha + 105 con) theo tuần & chia đều khung giờ
# ==============================================================================

set -e

# Xác định đường dẫn thư mục gốc dự án
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Tạo thư mục chứa logs nếu chưa có
LOG_DIR="$PROJECT_DIR/data/logs"
mkdir -p "$LOG_DIR"

# Nhận diện Python Virtual Environment
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
elif [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/python" ]; then
    PYTHON_BIN="$VIRTUAL_ENV/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "[LỖI] Không tìm thấy Python! Vui lòng cài đặt hoặc kích hoạt môi trường ảo (.venv)."
    exit 1
fi

# Cấu hình Proxy (nếu có): đọc từ biến môi trường PROXY_URL hoặc từ .env
if [ -z "$PROXY_URL" ] && [ -f "$PROJECT_DIR/.env" ]; then
    PROXY_FROM_ENV="$(grep -E '^PROXY_URL=' "$PROJECT_DIR/.env" | cut -d '=' -f2- | tr -d ' "' | tr -d "'")"
    if [ -n "$PROXY_FROM_ENV" ]; then
        PROXY_URL="$PROXY_FROM_ENV"
    fi
fi

PROXY_ARG=""
if [ -n "$PROXY_URL" ]; then
    echo "[PROXY] Kích hoạt Proxy: $PROXY_URL"
    export HTTP_PROXY="$PROXY_URL"
    export HTTPS_PROXY="$PROXY_URL"
    export ALL_PROXY="$PROXY_URL"
    PROXY_ARG="--proxy $PROXY_URL"
fi

CRON_MARKER="# === VNEXPRESS CRAWLER SCHEDULED JOBS ==="
CRON_END_MARKER="# === END VNEXPRESS CRAWLER JOBS ==="

# Hiển thị nội dung crontab tương ứng
generate_crontab_entries() {
    cat << EOF
$CRON_MARKER
# 1. Cào 100 tin mới nhất toàn trang qua RSS mỗi giờ (vào phút 00)
0 * * * * $PROJECT_DIR/Cronjob.sh hourly >> $LOG_DIR/cron_hourly.log 2>&1

# 2. Thứ 2 (Thời sự & Thế giới)
0 2 * * 1 $PROJECT_DIR/Cronjob.sh daily mon slot1 >> $LOG_DIR/cron_daily.log 2>&1
0 13 * * 1 $PROJECT_DIR/Cronjob.sh daily mon slot2 >> $LOG_DIR/cron_daily.log 2>&1

# 3. Thứ 3 (Kinh doanh & Bất động sản)
0 2 * * 2 $PROJECT_DIR/Cronjob.sh daily tue slot1 >> $LOG_DIR/cron_daily.log 2>&1
0 13 * * 2 $PROJECT_DIR/Cronjob.sh daily tue slot2 >> $LOG_DIR/cron_daily.log 2>&1

# 4. Thứ 4 (Khoa học Công nghệ & Xe)
0 2 * * 3 $PROJECT_DIR/Cronjob.sh daily wed slot1 >> $LOG_DIR/cron_daily.log 2>&1
0 13 * * 3 $PROJECT_DIR/Cronjob.sh daily wed slot2 >> $LOG_DIR/cron_daily.log 2>&1

# 5. Thứ 5 (Thể thao, Giải trí & Thư giãn)
0 2 * * 4 $PROJECT_DIR/Cronjob.sh daily thu slot1 >> $LOG_DIR/cron_daily.log 2>&1
0 13 * * 4 $PROJECT_DIR/Cronjob.sh daily thu slot2 >> $LOG_DIR/cron_daily.log 2>&1
0 20 * * 4 $PROJECT_DIR/Cronjob.sh daily thu slot3 >> $LOG_DIR/cron_daily.log 2>&1

# 6. Thứ 6 (Sức khỏe, Đời sống & Du lịch)
0 2 * * 5 $PROJECT_DIR/Cronjob.sh daily fri slot1 >> $LOG_DIR/cron_daily.log 2>&1
0 13 * * 5 $PROJECT_DIR/Cronjob.sh daily fri slot2 >> $LOG_DIR/cron_daily.log 2>&1
0 20 * * 5 $PROJECT_DIR/Cronjob.sh daily fri slot3 >> $LOG_DIR/cron_daily.log 2>&1

# 7. Thứ 7 (Giáo dục, Pháp luật, Xã hội, Ý kiến & Tâm sự)
0 2 * * 6 $PROJECT_DIR/Cronjob.sh daily sat slot1 >> $LOG_DIR/cron_daily.log 2>&1
0 13 * * 6 $PROJECT_DIR/Cronjob.sh daily sat slot2 >> $LOG_DIR/cron_daily.log 2>&1
0 20 * * 6 $PROJECT_DIR/Cronjob.sh daily sat slot3 >> $LOG_DIR/cron_daily.log 2>&1

# 8. Chủ nhật: Bảo trì & Đồng bộ
0 3 * * 0 $PROJECT_DIR/Cronjob.sh daily sun slot1 >> $LOG_DIR/cron_maint.log 2>&1
0 14 * * 0 $PROJECT_DIR/Cronjob.sh daily sun slot2 >> $LOG_DIR/cron_maint.log 2>&1
$CRON_END_MARKER
EOF
}

show_help() {
    echo "=========================================================================="
    echo "                 VNEXPRESS CRAWLER - CRONJOB CONTROLLER                   "
    echo "=========================================================================="
    echo "Cách dùng: ./Cronjob.sh <lệnh> [tham số]"
    echo ""
    echo "Các lệnh hỗ trợ:"
    echo "  schedule / plan          Xem bảng phân bổ lịch cào 122 danh mục trong tuần"
    echo "  hourly                   Cào 100 bài mới nhất ngay lập tức (Breaking RSS)"
    echo "  daily [day] [slot]       Cào chuyên mục theo ngày (mon, tue, wed, thu, fri, sat, sun, today)"
    echo "                           Kèm khung giờ: slot1, slot2, slot3 (nếu có)"
    echo "  maintenance              Bảo trì: đồng bộ lượt bình luận & tối ưu DB"
    echo "  all                      Cào toàn bộ 122 danh mục trong hệ thống (chạy tuần tự)"
    echo "  status / stats           Xem thống kê dữ liệu hiện tại trong hệ thống"
    echo ""
    echo "Lệnh quản lý Crontab hệ điều hành (Linux / macOS):"
    echo "  crontab-show             In ra toàn bộ cấu hình Crontab phân bổ theo khung giờ"
    echo "  install                  Tự động cài đặt lịch trình vào crontab của người dùng"
    echo "  uninstall                Xóa lịch trình cào tin khỏi crontab người dùng"
    echo "=========================================================================="
}

COMMAND="${1:-help}"

case "$COMMAND" in
    schedule|plan)
        "$PYTHON_BIN" -m crawler.cron --mode schedule
        ;;

    hourly)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Kích hoạt cào 100 bài mới nhất (RSS)..."
        "$PYTHON_BIN" -m crawler.cron --mode hourly --max-articles "${2:-100}" $PROXY_ARG
        ;;

    daily)
        DAY="${2:-today}"
        SLOT="$3"
        SLOT_ARG=""
        if [ -n "$SLOT" ]; then
            SLOT_ARG="--slot $SLOT"
        fi
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Kích hoạt cào danh mục theo ngày: $DAY (khung giờ: ${SLOT:-Tất cả})..."
        "$PYTHON_BIN" -m crawler.cron --mode daily --day "$DAY" $SLOT_ARG --max-articles 100 --pages 7 $PROXY_ARG
        ;;

    maintenance)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Kích hoạt bảo trì & đồng bộ dữ liệu..."
        "$PYTHON_BIN" -m crawler.cron --mode maintenance $PROXY_ARG
        ;;

    all)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Kích hoạt cào toàn bộ 122 danh mục (100 bài/mục)..."
        "$PYTHON_BIN" -m crawler.cron --mode all --max-articles 100 --pages 7 $PROXY_ARG
        ;;

    status|stats)
        "$PYTHON_BIN" -m crawler.cli stats
        ;;

    crontab-show)
        echo "=== CẤU HÌNH CRONTAB PHÂN BỔ KHUNG GIỜ HẰNG TUẦN ==="
        generate_crontab_entries
        ;;

    install)
        echo "--> Đang cài đặt lịch trình vào crontab hệ thống..."
        TEMP_CRON="$(mktemp)"
        crontab -l 2>/dev/null | sed "/$CRON_MARKER/,/$CRON_END_MARKER/d" > "$TEMP_CRON" || true
        generate_crontab_entries >> "$TEMP_CRON"
        crontab "$TEMP_CRON"
        rm -f "$TEMP_CRON"
        echo "[THÀNH CÔNG] Đã đăng ký lịch trình Cronjob vào hệ thống!"
        echo "Xem danh sách lịch đang chạy bằng lệnh: crontab -l"
        ;;

    uninstall)
        echo "--> Đang gỡ bỏ lịch trình khỏi crontab hệ thống..."
        TEMP_CRON="$(mktemp)"
        crontab -l 2>/dev/null | sed "/$CRON_MARKER/,/$CRON_END_MARKER/d" > "$TEMP_CRON" || true
        crontab "$TEMP_CRON"
        rm -f "$TEMP_CRON"
        echo "[THÀNH CÔNG] Đã gỡ bỏ cấu hình Cronjob của VnExpress Crawler khỏi crontab."
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo "Lệnh không hợp lệ: $COMMAND"
        show_help
        exit 1
        ;;
esac
