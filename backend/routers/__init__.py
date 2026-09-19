"""API Routers package."""

from backend.routers.articles import router as articles_router
from backend.routers.categories import router as categories_router
from backend.routers.crawler import router as crawler_router
from backend.routers.search import router as search_router

__all__ = ["categories_router", "articles_router", "search_router", "crawler_router"]
