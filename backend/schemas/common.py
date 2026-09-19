"""Common DTO schemas for responses and pagination."""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int = Field(..., description="Tổng số bản ghi thỏa mãn điều kiện")
    page: int = Field(..., description="Trang hiện tại (1-based)")
    page_size: int = Field(..., description="Số bản ghi trên mỗi trang")
    total_pages: int = Field(..., description="Tổng số trang")


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: int = 400


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
