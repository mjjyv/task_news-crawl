"""Article router endpoints."""

from datetime import datetime
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.dependencies import get_article_service
from backend.schemas.article import ArticleDetail, ArticleSummary
from backend.schemas.common import PaginatedResponse
from backend.services.article_service import ArticleService

router = APIRouter(tags=["Articles"])


@router.get(
    "",
    response_model=PaginatedResponse[ArticleSummary],
    summary="Lấy danh sách bài viết phân trang & bộ lọc",
)
def list_articles(
    category: Optional[str] = Query(
        None,
        description="Lọc theo slug chuyên mục (bao gồm cả các chuyên mục con, vd: 'thoi-su')",
    ),
    from_date: Optional[datetime] = Query(
        None,
        description="Lọc bài viết từ thời điểm (ISO 8601, vd: '2026-03-01T00:00:00')",
    ),
    to_date: Optional[datetime] = Query(
        None,
        description="Lọc bài viết đến thời điểm (ISO 8601, vd: '2026-03-31T23:59:59')",
    ),
    page: int = Query(1, ge=1, description="Số trang hiện tại (bắt đầu từ 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng bài viết trên mỗi trang (1-100)"),
    order: Literal["desc", "asc"] = Query(
        "desc",
        description="Thứ tự sắp xếp theo thời gian xuất bản: 'desc' (mới nhất) hoặc 'asc' (cũ nhất)",
    ),
    service: ArticleService = Depends(get_article_service),
) -> PaginatedResponse[ArticleSummary]:
    """
    Lấy danh sách bài viết tổng hợp có phân trang.

    Hỗ trợ lọc theo:
    - **category**: Slug danh mục (tự động đệ quy bao gồm bài viết của các danh mục con).
    - **from_date** / **to_date**: Khoảng thời gian xuất bản.
    - **order**: Sắp xếp tăng/giảm dần theo ngày xuất bản.
    """
    return service.get_articles(
        category_slug=category,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        order=order,
    )


@router.get(
    "/{id}",
    response_model=ArticleDetail,
    summary="Chi tiết bài viết kèm media & bài liên quan",
)
def get_article_detail(
    id: int,
    service: ArticleService = Depends(get_article_service),
) -> ArticleDetail:
    """
    Lấy toàn bộ nội dung chi tiết của bài viết theo ID.

    Bao gồm:
    - Nội dung văn bản thuần (`content_text`) & HTML chuẩn hóa (`content_html`).
    - Danh sách hình ảnh / video đính kèm (`media`).
    - Danh sách các bài viết liên quan trong cùng chuyên mục (`related_articles`).
    """
    article = service.get_article_detail(id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bài viết với ID {id} không tồn tại.",
        )
    return article
