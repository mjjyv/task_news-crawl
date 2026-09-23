"""Article business logic service."""

from datetime import datetime
import math
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.schemas.article import (
    ArticleDetail,
    ArticleSummary,
    CategoryShort,
    CommentResponse,
    MediaResponse,
)
from backend.schemas.common import PaginatedResponse
from backend.services.category_service import CategoryService
from crawler.storage.models import Article, Category


class ArticleService:
    """Service handling article listing, filtering, pagination, and detail views."""

    def __init__(self, session: Session):
        self.session = session
        self.category_service = CategoryService(session)

    def get_articles(
        self,
        category_slug: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        min_comments: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        order: str = "desc",
        sort: str = "latest",
    ) -> PaginatedResponse[ArticleSummary]:
        """Fetch paginated articles with optional category, date range, and hotness filters."""
        page = max(1, page)
        page_size = min(max(1, page_size), 100)

        stmt = select(Article).options(selectinload(Article.category))
        count_stmt = select(func.count(Article.id))

        # 1. Filter by category (including subcategories)
        if category_slug:
            cat = self.session.execute(
                select(Category).where(Category.slug == category_slug)
            ).scalar_one_or_none()
            if cat:
                cat_ids = self.category_service.get_descendant_category_ids(cat.id)
                stmt = stmt.where(Article.category_id.in_(cat_ids))
                count_stmt = count_stmt.where(Article.category_id.in_(cat_ids))
            else:
                # Category slug doesn't exist -> empty result
                return PaginatedResponse(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                )

        # 2. Date filters
        if from_date:
            stmt = stmt.where(Article.published_at >= from_date)
            count_stmt = count_stmt.where(Article.published_at >= from_date)
        if to_date:
            stmt = stmt.where(Article.published_at <= to_date)
            count_stmt = count_stmt.where(Article.published_at <= to_date)

        # 3. Minimum comments filter (for finding hot articles)
        if min_comments is not None and min_comments > 0:
            stmt = stmt.where(Article.comment_count >= min_comments)
            count_stmt = count_stmt.where(Article.comment_count >= min_comments)

        # 4. Total count
        total = self.session.execute(count_stmt).scalar() or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # 5. Sorting & pagination
        if sort.lower() == "hot" or order.lower() == "hot":
            stmt = stmt.order_by(Article.comment_count.desc(), Article.published_at.desc().nulls_last())
        elif sort.lower() == "oldest" or order.lower() == "asc":
            stmt = stmt.order_by(Article.published_at.asc().nulls_last())
        else:
            stmt = stmt.order_by(Article.published_at.desc().nulls_last())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        articles = self.session.execute(stmt).scalars().all()

        items = [
            ArticleSummary(
                id=a.id,
                title=a.title,
                slug=a.slug,
                description=a.description,
                thumbnail_url=a.thumbnail_url,
                author=a.author,
                origin_url=a.origin_url,
                published_at=a.published_at,
                comment_count=a.comment_count,
                post_type=getattr(a, "post_type", "text") or "text",
                category=CategoryShort.model_validate(a.category) if a.category else None,
            )
            for a in articles
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_article_detail(self, article_id: int) -> Optional[ArticleDetail]:
        """Fetch article detail with media, comments, and related articles."""
        import json

        stmt = (
            select(Article)
            .options(
                selectinload(Article.category),
                selectinload(Article.media),
                selectinload(Article.comments),
            )
            .where(Article.id == article_id)
        )
        article = self.session.execute(stmt).scalar_one_or_none()
        if not article:
            return None

        # Parse saved related article IDs
        rel_ids: List[int] = []
        if getattr(article, "related_article_ids", None):
            try:
                parsed_ids = json.loads(article.related_article_ids)
                if isinstance(parsed_ids, list):
                    rel_ids = [int(x) for x in parsed_ids if str(x).isdigit()]
            except Exception:
                rel_ids = []

        # Related articles: first attempt to load articles matching rel_ids from DB
        related_items: List[ArticleSummary] = []
        loaded_ids = set()
        if rel_ids:
            rel_stmt = (
                select(Article)
                .options(selectinload(Article.category))
                .where(Article.id.in_(rel_ids), Article.id != article.id)
                .limit(10)
            )
            rel_matches = self.session.execute(rel_stmt).scalars().all()
            for r in rel_matches:
                loaded_ids.add(r.id)
                related_items.append(
                    ArticleSummary(
                        id=r.id,
                        title=r.title,
                        slug=r.slug,
                        description=r.description,
                        thumbnail_url=r.thumbnail_url,
                        author=r.author,
                        origin_url=r.origin_url,
                        published_at=r.published_at,
                        comment_count=r.comment_count,
                        post_type=getattr(r, "post_type", "text") or "text",
                        category=CategoryShort.model_validate(r.category) if r.category else None,
                    )
                )

        # Fallback to fill up to 5 articles from same category if fewer found
        if len(related_items) < 5 and article.category_id:
            fallback_limit = 5 - len(related_items)
            exclude_ids = {article.id} | loaded_ids
            fb_stmt = (
                select(Article)
                .options(selectinload(Article.category))
                .where(
                    Article.category_id == article.category_id,
                    Article.id.not_in(exclude_ids),
                )
                .order_by(Article.published_at.desc().nulls_last())
                .limit(fallback_limit)
            )
            fb_articles = self.session.execute(fb_stmt).scalars().all()
            for r in fb_articles:
                related_items.append(
                    ArticleSummary(
                        id=r.id,
                        title=r.title,
                        slug=r.slug,
                        description=r.description,
                        thumbnail_url=r.thumbnail_url,
                        author=r.author,
                        origin_url=r.origin_url,
                        published_at=r.published_at,
                        comment_count=r.comment_count,
                        post_type=getattr(r, "post_type", "text") or "text",
                        category=CategoryShort.model_validate(r.category) if r.category else None,
                    )
                )

        media_dtos = [MediaResponse.model_validate(m) for m in article.media]

        # Sort comments by likes DESC, then created_at DESC
        sorted_comments = sorted(
            article.comments,
            key=lambda c: (c.likes, c.created_at.timestamp() if c.created_at else 0),
            reverse=True,
        )
        comment_dtos = [CommentResponse.model_validate(c) for c in sorted_comments]

        return ArticleDetail(
            id=article.id,
            title=article.title,
            slug=article.slug,
            description=article.description,
            content_html=article.content_html,
            content_text=article.content_text,
            author=article.author,
            thumbnail_url=article.thumbnail_url,
            origin_url=article.origin_url,
            published_at=article.published_at,
            comment_count=article.comment_count,
            post_type=getattr(article, "post_type", "text") or "text",
            created_at=article.created_at,
            category=CategoryShort.model_validate(article.category) if article.category else None,
            media=media_dtos,
            related_article_ids=rel_ids,
            related_articles=related_items,
            comments=comment_dtos,
        )
