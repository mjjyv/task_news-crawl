"""Category router endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.dependencies import get_category_service
from backend.schemas.category import CategoryDetailResponse, CategoryTreeItem
from backend.services.category_service import CategoryService

router = APIRouter(tags=["Categories"])


@router.get("", response_model=List[CategoryTreeItem], summary="Lấy danh mục bài viết")
def list_categories(
    tree: bool = Query(default=True, description="Trả về dạng cây phân cấp (true) hoặc danh sách phẳng (false)"),
    service: CategoryService = Depends(get_category_service),
) -> List[CategoryTreeItem]:
    """
    Lấy danh sách tất cả các danh mục tin tức.

    - **tree=true** (mặc định): Trả về cấu trúc cây cha - con, số bài viết được cộng dồn từ nhánh con.
    - **tree=false**: Trả về danh sách phẳng các danh mục kèm số bài viết trực tiếp.
    """
    return service.get_categories(tree=tree)


@router.get("/{slug:path}", response_model=CategoryDetailResponse, summary="Chi tiết danh mục theo slug")
def get_category_by_slug(
    slug: str,
    service: CategoryService = Depends(get_category_service),
) -> CategoryDetailResponse:
    """
    Lấy chi tiết danh mục theo slug (hỗ trợ cả slug cha như 'thoi-su' lẫn slug con như 'thoi-su/chinh-tri').

    Trả về thông tin danh mục, danh mục cha, danh mục con trực tiếp và tổng số bài viết.
    """
    cat = service.get_category_by_slug(slug)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danh mục với slug '{slug}' không tồn tại.",
        )
    return cat
