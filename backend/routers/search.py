"""Search router endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_search_service
from backend.schemas.search import SearchResponse
from backend.services.search_service import SearchService

router = APIRouter(tags=["Search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Tìm kiếm toàn văn tiếng Việt (Full-text & Multi-field)",
)
def search_articles(
    q: str = Query(
        ...,
        min_length=1,
        description="Từ khóa tìm kiếm tiếng Việt (có dấu hoặc không dấu, ví dụ: 'trí tuệ nhân tạo' hoặc 'tri tue nhan tao')",
    ),
    category: Optional[str] = Query(
        None,
        description="Lọc trong danh mục cụ thể theo slug (ví dụ: 'khoa-hoc')",
    ),
    exact_accent: bool = Query(
        False,
        description="Chế độ chỉ tìm kiếm chính xác có dấu (true) hoặc tìm kiếm không phân biệt dấu (false, mặc định)",
    ),
    page: int = Query(1, ge=1, description="Số trang hiện tại (bắt đầu từ 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng kết quả trên mỗi trang (1-100)"),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """
    Tìm kiếm bài viết đa trường (tiêu đề, tóm tắt, nội dung chi tiết) thông minh:

    - **Hỗ trợ tìm kiếm có dấu chính xác & không dấu**:
      - `exact_accent=false` (mặc định): Tìm kiếm không phân biệt dấu (ví dụ: 'tri tue' khớp 'trí tuệ').
      - `exact_accent=true`: Chỉ tìm kiếm chính xác các từ có dấu (ví dụ: 'ngủ' chỉ khớp đúng từ 'ngủ', không lấy 'ngũ' hay 'ngu').
    - **Trích xuất đoạn trích (Snippet)**: Trả về câu văn chứa từ khóa ngữ cảnh trực tiếp.
    - **Lọc theo danh mục**: Giới hạn phạm vi tìm kiếm theo chuyên mục.
    """
    return service.search(
        query=q,
        category_slug=category,
        exact_accent=exact_accent,
        page=page,
        page_size=page_size,
    )
