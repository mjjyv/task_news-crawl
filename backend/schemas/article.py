"""Article DTO schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class MediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str  # 'image', 'video', 'audio'
    url: str
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ArticleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    origin_url: str
    published_at: Optional[datetime] = None
    comment_count: int = 0
    category: Optional[CategoryShort] = None


class ArticleDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: Optional[str] = None
    content_html: str
    content_text: str
    author: Optional[str] = None
    thumbnail_url: Optional[str] = None
    origin_url: str
    published_at: Optional[datetime] = None
    comment_count: int = 0
    created_at: Optional[datetime] = None
    category: Optional[CategoryShort] = None
    media: List[MediaResponse] = Field(default_factory=list)
    related_articles: List[ArticleSummary] = Field(default_factory=list)
