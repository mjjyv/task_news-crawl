"""Pipeline to backfill and enrich existing articles with missing media, rich post types, comments, and related articles."""

import logging
import time
from typing import Any, Dict, List, Optional

from crawler.config import settings
from crawler.http_client import HttpClient
from crawler.parsers.article import ArticleParser
from crawler.storage.database import get_db_session
from crawler.storage.models import Article
from crawler.storage.repository import Repository

logger = logging.getLogger(__name__)


class ArticleBackfillPipeline:
    """Manages backfilling and updating existing articles in the database."""

    def __init__(
        self,
        http_client: Optional[HttpClient] = None,
        article_parser: Optional[ArticleParser] = None,
        proxy_url: Optional[str] = None,
    ):
        self.http_client = http_client or HttpClient(proxy_url=proxy_url)
        self.article_parser = article_parser or ArticleParser(base_url=settings.base_url)

    def backfill_single_article(
        self, article_id: int, html_content: Optional[str] = None
    ) -> bool:
        """Backfill a single article by ID.
        If html_content is provided, parses it directly without making an HTTP request.
        """
        with get_db_session() as session:
            repo = Repository(session)
            article = repo.get_article_by_id(article_id)
            if not article:
                logger.warning("Article with ID %d not found in database.", article_id)
                return False

            origin_url = article.origin_url
            cat_slug = article.category.slug if article.category else None

            # Fetch HTML if not passed directly
            if not html_content:
                try:
                    logger.info("Fetching article for backfill [%d]: %s", article_id, origin_url)
                    resp = self.http_client.fetch(origin_url)
                    html_content = resp.text
                except Exception as exc:
                    logger.error("Failed to fetch article [%d] from %s: %s", article_id, origin_url, exc)
                    repo.log_crawl("backfill", origin_url, "failed", error_message=str(exc))
                    return False

            # Parse article detail
            try:
                parsed = self.article_parser.parse(
                    html=html_content,
                    url=origin_url,
                )
                if not parsed:
                    logger.warning("ArticleParser returned None for article [%d]", article_id)
                    return False

                # Prepare updated attributes
                art_update: Dict[str, Any] = {
                    "id": article.id,
                    "post_type": parsed.post_type,
                    "related_article_ids": parsed.related_article_ids,
                }

                # Update thumbnail if currently missing
                if not article.thumbnail_url and parsed.thumbnail_url:
                    art_update["thumbnail_url"] = parsed.thumbnail_url

                # Update comment count if parsed higher
                if parsed.comment_count and parsed.comment_count > article.comment_count:
                    art_update["comment_count"] = parsed.comment_count

                # Prepare media and comments
                media_dicts = [m.model_dump() for m in parsed.media]
                comment_dicts = [c.model_dump() for c in parsed.comments]

                repo.upsert_article(art_update, media_dicts, comment_dicts)
                session.commit()
                logger.info(
                    "Backfilled article [%d]: post_type='%s', media=%d, comments=%d, related=%d",
                    article.id,
                    parsed.post_type,
                    len(media_dicts),
                    len(comment_dicts),
                    len(parsed.related_article_ids),
                )
                return True
            except Exception as exc:
                logger.error("Error during backfill parse/save for article [%d]: %s", article_id, exc)
                repo.log_crawl("backfill", origin_url, "failed", error_message=str(exc))
                return False

    def backfill_articles_by_ids(
        self, article_ids: List[int], delay: float = 0.5
    ) -> Dict[str, int]:
        """Backfill a list of article IDs with polite delay."""
        total = len(article_ids)
        updated = 0
        failed = 0

        logger.info("Starting batch backfill for %d articles...", total)
        for idx, aid in enumerate(article_ids, start=1):
            success = self.backfill_single_article(aid)
            if success:
                updated += 1
            else:
                failed += 1

            if idx < total and delay > 0:
                time.sleep(delay)

        return {"total": total, "updated": updated, "failed": failed}

    def backfill_missing_media(
        self, limit: int = 50, category_id: Optional[int] = None, delay: float = 0.5
    ) -> Dict[str, int]:
        """Find articles with zero media in DB and re-fetch to extract media."""
        with get_db_session() as session:
            repo = Repository(session)
            articles = repo.get_articles_without_media(limit=limit, category_id=category_id)
            target_ids = [a.id for a in articles]

        logger.info("Found %d articles with missing media (limit=%d).", len(target_ids), limit)
        return self.backfill_articles_by_ids(target_ids, delay=delay)

    def backfill_rich_posts(
        self, limit: int = 50, category_id: Optional[int] = None, delay: float = 0.5
    ) -> Dict[str, int]:
        """Find articles that likely contain slideshows/infographics and backfill high-res media."""
        with get_db_session() as session:
            repo = Repository(session)
            articles = repo.get_articles_missing_rich_metadata(limit=limit, category_id=category_id)
            target_ids = [a.id for a in articles]

        logger.info("Found %d rich candidate articles (limit=%d).", len(target_ids), limit)
        return self.backfill_articles_by_ids(target_ids, delay=delay)

    def backfill_comments(
        self, limit: int = 50, category_id: Optional[int] = None, delay: float = 0.5
    ) -> Dict[str, int]:
        """Find articles with comment_count > 0 but zero stored comments and backfill them."""
        with get_db_session() as session:
            repo = Repository(session)
            articles = repo.get_articles_without_comments(limit=limit, category_id=category_id)
            target_ids = [a.id for a in articles]

        logger.info("Found %d articles with uncollected comments (limit=%d).", len(target_ids), limit)
        return self.backfill_articles_by_ids(target_ids, delay=delay)

    def backfill_all(self, limit: int = 50, delay: float = 0.5) -> Dict[str, int]:
        """Backfill across all categories: missing media, rich posts, and comments."""
        res_media = self.backfill_missing_media(limit=limit, delay=delay)
        res_rich = self.backfill_rich_posts(limit=limit, delay=delay)
        res_comments = self.backfill_comments(limit=limit, delay=delay)

        total_updated = res_media["updated"] + res_rich["updated"] + res_comments["updated"]
        total_failed = res_media["failed"] + res_rich["failed"] + res_comments["failed"]
        return {
            "total": res_media["total"] + res_rich["total"] + res_comments["total"],
            "updated": total_updated,
            "failed": total_failed,
        }
