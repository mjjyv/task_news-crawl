"""Pydantic v2 schemas for Backend API."""

from backend.schemas.article import ArticleDetail, ArticleSummary, MediaResponse
from backend.schemas.category import CategoryDetailResponse, CategoryTreeItem
from backend.schemas.common import ErrorResponse, PaginatedResponse, SuccessResponse
from backend.schemas.crawler import CrawlerHealthResponse, CrawlTriggerRequest, CrawlTriggerResponse
from backend.schemas.search import SearchResponse, SearchResultItem

__all__ = [
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "CategoryTreeItem",
    "CategoryDetailResponse",
    "ArticleSummary",
    "ArticleDetail",
    "MediaResponse",
    "SearchResultItem",
    "SearchResponse",
    "CrawlerHealthResponse",
    "CrawlTriggerRequest",
    "CrawlTriggerResponse",
]
