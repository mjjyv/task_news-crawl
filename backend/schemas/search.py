"""Search DTO schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.schemas.article import CategoryShort


class SearchResultItem(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[CategoryShort] = None
    score: float = Field(default=1.0, description="Độ liên quan của kết quả tìm kiếm")
    snippet: Optional[str] = Field(default=None, description="Đoạn văn bản chứa từ khóa tìm kiếm")


class SearchResponse(BaseModel):
    query: str
    exact_accent: bool = Field(default=False, description="Chế độ tìm kiếm: true (chỉ tìm chính xác có dấu), false (không phân biệt dấu/mở rộng)")
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[SearchResultItem]
