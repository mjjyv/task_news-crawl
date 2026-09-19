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
        """Fetch article detail with media and related articles."""
        stmt = (
            select(Article)
            .options(
                selectinload(Article.category),
                selectinload(Article.media),
            )
            .where(Article.id == article_id)
        )
        article = self.session.execute(stmt).scalar_one_or_none()
        if not article:
            return None

        # Related articles (up to 5 in same category, excluding current)
        related_items: List[ArticleSummary] = []
        if article.category_id:
            rel_stmt = (
                select(Article)
                .options(selectinload(Article.category))
                .where(
                    Article.category_id == article.category_id,
                    Article.id != article.id,
                )
                .order_by(Article.published_at.desc().nulls_last())
                .limit(5)
            )
            related_articles = self.session.execute(rel_stmt).scalars().all()
            related_items = [
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
                    category=CategoryShort.model_validate(r.category) if r.category else None,
                )
                for r in related_articles
            ]

        media_dtos = [MediaResponse.model_validate(m) for m in article.media]

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
            created_at=article.created_at,
            category=CategoryShort.model_validate(article.category) if article.category else None,
            media=media_dtos,
            related_articles=related_items,
        )
