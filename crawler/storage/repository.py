"""Data Access Repository for Articles, Categories, Media, and CrawlLogs."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crawler.storage.models import Article, Category, CrawlLog, Media

logger = logging.getLogger(__name__)


class Repository:
    """Repository handling CRUD operations on DB entities."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------ CATEGORIES ------------------

    def upsert_category(
        self,
        name: str,
        slug: str,
        origin_url: str,
        parent_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Category:
        """Create or update category by slug."""
        stmt = select(Category).where(Category.slug == slug)
        cat = self.session.execute(stmt).scalar_one_or_none()
        if cat:
            cat.name = name
            cat.origin_url = origin_url
            if parent_id is not None:
                cat.parent_id = parent_id
            if description is not None:
                cat.description = description
        else:
            cat = Category(
                name=name,
                slug=slug,
                origin_url=origin_url,
                parent_id=parent_id,
                description=description,
            )
            self.session.add(cat)
        self.session.flush()
        return cat

    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        stmt = select(Category).where(Category.slug == slug)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_category_by_id(self, cat_id: int) -> Optional[Category]:
        return self.session.get(Category, cat_id)

    def get_all_categories(self, top_level_only: bool = False) -> List[Category]:
        stmt = select(Category)
        if top_level_only:
            stmt = stmt.where(Category.parent_id.is_(None))
        stmt = stmt.order_by(Category.name)
        return list(self.session.execute(stmt).scalars().all())

    def get_subcategories(self, parent_id: int) -> List[Category]:
        """Get all child subcategories for a given parent category ID."""
        stmt = select(Category).where(Category.parent_id == parent_id).order_by(Category.name)
        return list(self.session.execute(stmt).scalars().all())


    # ------------------ ARTICLES ------------------

    def upsert_article(
        self,
        article_data: Dict[str, Any],
        media_items: Optional[List[Dict[str, Any]]] = None,
    ) -> Article:
        """Create or update article by ID."""
        art_id = article_data["id"]
        stmt = select(Article).where(Article.id == art_id)
        article = self.session.execute(stmt).scalar_one_or_none()

        if article:
            for key, val in article_data.items():
                setattr(article, key, val)
        else:
            article = Article(**article_data)
            self.session.add(article)

        self.session.flush()

        # Add media if provided
        if media_items:
            existing_urls = {m.url for m in article.media}
            for m in media_items:
                if m.get("url") and m["url"] not in existing_urls:
                    media_obj = Media(
                        article=article,
                        type=m.get("type", "image"),
                        url=m["url"],
                        caption=m.get("caption"),
                        width=m.get("width"),
                        height=m.get("height"),
                        local_path=m.get("local_path"),
                    )
                    self.session.add(media_obj)
                    existing_urls.add(m["url"])

        self.session.flush()
        return article

    def get_article_by_id(self, art_id: int) -> Optional[Article]:
        return self.session.get(Article, art_id)

    def get_articles(
        self,
        category_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        stmt = select(Article)
        if category_id is not None:
            stmt = stmt.where(Article.category_id == category_id)
        stmt = stmt.order_by(Article.published_at.desc().nulls_last()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def count_articles(self, category_id: Optional[int] = None) -> int:
        stmt = select(func.count(Article.id))
        if category_id is not None:
            stmt = stmt.where(Article.category_id == category_id)
        return self.session.execute(stmt).scalar() or 0

    # ------------------ CRAWL LOGS ------------------

    def log_crawl(
        self,
        crawler_type: str,
        target_url: str,
        status: str,
        articles_found: int = 0,
        articles_new: int = 0,
        error_message: Optional[str] = None,
    ) -> CrawlLog:
        log = CrawlLog(
            crawler_type=crawler_type,
            target_url=target_url,
            status=status,
            articles_found=articles_found,
            articles_new=articles_new,
            error_message=error_message,
        )
        self.session.add(log)
        self.session.flush()
        return log

    # ------------------ STATS ------------------

    def get_stats(self) -> Dict[str, Any]:
        cat_count = self.session.execute(select(func.count(Category.id))).scalar() or 0
        art_count = self.session.execute(select(func.count(Article.id))).scalar() or 0
        media_count = self.session.execute(select(func.count(Media.id))).scalar() or 0
        latest_logs = self.session.execute(
            select(CrawlLog).order_by(CrawlLog.executed_at.desc()).limit(5)
        ).scalars().all()

        return {
            "total_categories": cat_count,
            "total_articles": art_count,
            "total_media": media_count,
            "latest_logs": [
                {
                    "type": l.crawler_type,
                    "target": l.target_url,
                    "status": l.status,
                    "found": l.articles_found,
                    "new": l.articles_new,
                    "time": l.executed_at.isoformat() if l.executed_at else None,
                }
                for l in latest_logs
            ],
        }
