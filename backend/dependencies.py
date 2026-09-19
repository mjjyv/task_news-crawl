"""FastAPI dependency injection providers."""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.services.article_service import ArticleService
from backend.services.category_service import CategoryService
from backend.services.crawler_service import CrawlerService
from backend.services.search_service import SearchService
from crawler.storage.database import get_db_session


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session."""
    with get_db_session() as session:
        yield session


def get_category_service(session: Session = Depends(get_db)) -> CategoryService:
    return CategoryService(session)


def get_article_service(session: Session = Depends(get_db)) -> ArticleService:
    return ArticleService(session)


def get_search_service(session: Session = Depends(get_db)) -> SearchService:
    return SearchService(session)


def get_crawler_service(session: Session = Depends(get_db)) -> CrawlerService:
    return CrawlerService(session)
