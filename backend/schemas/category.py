"""Category DTO schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    origin_url: str
    parent_id: Optional[int] = None
    description: Optional[str] = None


class CategoryTreeItem(CategoryBase):
    children: List["CategoryTreeItem"] = Field(default_factory=list)
    article_count: int = 0


class CategoryDetailResponse(CategoryBase):
    parent: Optional[CategoryBase] = None
    children: List[CategoryBase] = Field(default_factory=list)
    article_count: int = 0
