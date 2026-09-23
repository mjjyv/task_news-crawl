"""Crawler monitoring and management DTO schemas."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class CrawlLogItem(BaseModel):
    id: int
    crawler_type: str
    target_url: str
    status: str
    articles_found: int
    articles_new: int
    error_message: Optional[str] = None
    executed_at: Optional[datetime] = None


class CrawlerHealthResponse(BaseModel):
    status: str = "healthy"  # 'healthy', 'degraded', 'unhealthy'
    database_connected: bool
    redis_connected: bool
    deduplicator_type: str
    total_categories: int
    total_articles: int
    total_media: int
    total_comments: int = 0
    seen_ids_count: int
    latest_logs: List[CrawlLogItem] = Field(default_factory=list)


class CrawlTriggerRequest(BaseModel):
    type: Literal["rss", "category"] = Field(default="rss", description="Loại cào: 'rss' hoặc 'category'")
    target: str = Field(default="tin-moi-nhat", description="Topic RSS hoặc slug chuyên mục")
    pages: Optional[int] = Field(default=1, ge=1, le=20, description="Số trang cần duyệt (chỉ dùng cho category)")
    max_articles: Optional[int] = Field(default=10, ge=1, le=50, description="Số lượng bài tối đa cần cào")


class CrawlTriggerResponse(BaseModel):
    status: str = "accepted"
    message: str
    task_type: str
    target: str


class BackfillTriggerRequest(BaseModel):
    mode: Literal["missing-media", "rich-posts", "comments", "all"] = Field(
        default="missing-media", description="Chế độ quét bài: missing-media, rich-posts, comments, all"
    )
    limit: int = Field(default=50, ge=1, le=500, description="Số lượng bài tối đa cần backfill")
    category: Optional[str] = Field(default=None, description="Lọc theo slug chuyên mục cụ thể")
    delay: float = Field(default=0.5, ge=0.0, le=5.0, description="Thời gian chờ giữa các bài viết (giây)")


class BackfillTriggerResponse(BaseModel):
    status: str = "accepted"
    message: str
    mode: str
    limit: int
