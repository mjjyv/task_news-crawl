"""Data Access Repository for Articles, Categories, Media, and CrawlLogs."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crawler.storage.models import Article, Category, Comment, CrawlLog, Media

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
        comments: Optional[List[Dict[str, Any]]] = None,
    ) -> Article:
        """Create or update article by ID, including media and comments."""
        import json

        art_id = article_data["id"]
        stmt = select(Article).where(Article.id == art_id)
        article = self.session.execute(stmt).scalar_one_or_none()

        # Serialize related_article_ids if list/set
        if "related_article_ids" in article_data and isinstance(
            article_data["related_article_ids"], (list, set)
        ):
            article_data["related_article_ids"] = json.dumps(list(article_data["related_article_ids"]))

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

        # Add or upsert comments if provided
        if comments:
            existing_cids = {c.id for c in article.comments}
            for c in comments:
                cid = c.get("id")
                if not cid:
                    continue
                if cid in existing_cids:
                    cmt = next((item for item in article.comments if item.id == cid), None)
                    if cmt:
                        cmt.likes = c.get("likes", cmt.likes)
                        cmt.reply_count = c.get("reply_count", cmt.reply_count)
                else:
                    cmt_obj = Comment(
                        id=cid,
                        article=article,
                        user_name=c.get("user_name", "Ẩn danh"),
                        user_avatar=c.get("user_avatar"),
                        content=c.get("content", ""),
                        likes=c.get("likes", 0),
                        time_str=c.get("time_str"),
                        reply_count=c.get("reply_count", 0),
                        parent_id=c.get("parent_id"),
                    )
                    self.session.add(cmt_obj)
                    existing_cids.add(cid)

        self.session.flush()
        return article

    def get_comments_by_article(self, article_id: int) -> List[Comment]:
        """Fetch comments for a given article, ordered by likes DESC, created_at DESC."""
        stmt = (
            select(Comment)
            .where(Comment.article_id == article_id)
            .order_by(Comment.likes.desc(), Comment.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def save_comments(self, article_id: int, comments: List[Dict[str, Any]]) -> int:
        """Upsert comments for an article."""
        article = self.session.get(Article, article_id)
        if not article:
            return 0
        existing_cids = {c.id for c in article.comments}
        added_count = 0
        for c in comments:
            cid = c.get("id")
            if not cid:
                continue
            if cid in existing_cids:
                cmt = next((item for item in article.comments if item.id == cid), None)
                if cmt:
                    cmt.likes = c.get("likes", cmt.likes)
                    cmt.reply_count = c.get("reply_count", cmt.reply_count)
            else:
                cmt_obj = Comment(
                    id=cid,
                    article=article,
                    user_name=c.get("user_name", "Ẩn danh"),
                    user_avatar=c.get("user_avatar"),
                    content=c.get("content", ""),
                    likes=c.get("likes", 0),
                    time_str=c.get("time_str"),
                    reply_count=c.get("reply_count", 0),
                    parent_id=c.get("parent_id"),
                )
                self.session.add(cmt_obj)
                existing_cids.add(cid)
                added_count += 1
        self.session.flush()
        return added_count

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
        comment_count = self.session.execute(select(func.count(Comment.id))).scalar() or 0
        latest_logs = self.session.execute(
            select(CrawlLog).order_by(CrawlLog.executed_at.desc()).limit(5)
        ).scalars().all()

        return {
            "total_categories": cat_count,
            "total_articles": art_count,
            "total_media": media_count,
            "total_comments": comment_count,
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
