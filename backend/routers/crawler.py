"""Crawler monitoring and execution router endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from backend.dependencies import get_crawler_service
from backend.schemas.crawler import (
    CrawlerHealthResponse,
    CrawlTriggerRequest,
    CrawlTriggerResponse,
)
from backend.services.crawler_service import CrawlerService

router = APIRouter(tags=["Crawler"])


@router.get(
    "/health",
    response_model=CrawlerHealthResponse,
    summary="Trạng thái hệ thống & thông số Crawler (Health Dashboard)",
)
def get_crawler_health(
    service: CrawlerService = Depends(get_crawler_service),
) -> CrawlerHealthResponse:
    """
    Kiểm tra tình trạng toàn bộ hệ thống:

    - Kết nối cơ sở dữ liệu (SQLite / PostgreSQL)
    - Trạng thái Redis deduplicator (hoặc in-memory fallback)
    - Tổng số danh mục, bài viết, media đã lưu trữ
    - Danh sách nhật ký cào tin gần nhất (`latest_logs`)
    """
    return service.get_health()


@router.post(
    "/trigger",
    response_model=CrawlTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Kích hoạt tác vụ cào tin tức chạy ngầm (Background Task)",
)
def trigger_crawl_task(
    payload: CrawlTriggerRequest,
    background_tasks: BackgroundTasks,
) -> CrawlTriggerResponse:
    """
    Kích hoạt một tiến trình cào dữ liệu mới chạy bất đồng bộ trong nền:

    - **type**: `rss` (cào theo RSS feed topic) hoặc `category` (cào theo danh mục phân trang).
    - **target**: Tên topic RSS (vd: `tin-moi-nhat`, `thoi-su`) hoặc slug chuyên mục (vd: `khoa-hoc`).
    - **pages**: Số trang cần duyệt (chỉ dùng cho category, mặc định 1).
    - **max_articles**: Giới hạn số bài viết tối đa cần lấy.
    """
    background_tasks.add_task(
        CrawlerService.execute_crawl_task,
        task_type=payload.type,
        target=payload.target,
        pages=payload.pages or 1,
        max_articles=payload.max_articles or 10,
    )

    return CrawlTriggerResponse(
        status="accepted",
        message=f"Tác vụ cào tin {payload.type} cho mục '{payload.target}' đã được xếp lịch chạy nền thành công.",
        task_type=payload.type,
        target=payload.target,
    )
