"""Crawler health check and background task execution service."""

import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.schemas.crawler import CrawlerHealthResponse, CrawlLogItem
from crawler.config import settings
from crawler.deduplicator import RedisDeduplicator, get_deduplicator
from crawler.pipeline.article_pipeline import ArticlePipeline
from crawler.storage.repository import Repository

logger = logging.getLogger(__name__)


class CrawlerService:
    """Service to monitor system health and trigger background crawl jobs."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = Repository(session)

    def get_health(self) -> CrawlerHealthResponse:
        """Inspect database, redis, and data ingestion metrics."""
        # 1. DB connection check
        db_ok = True
        try:
            self.session.execute(text("SELECT 1"))
        except Exception as exc:
            logger.error("DB health check failed: %s", exc)
            db_ok = False

        # 2. Redis connection check
        redis_ok = False
        dedup = get_deduplicator()
        if isinstance(dedup, RedisDeduplicator):
            redis_ok = True
        dedup_type = "Redis Set" if redis_ok else "Local In-Memory"

        # 3. Overall stats
        stats = self.repo.get_stats()
        seen_count = dedup.count()

        status = "healthy"
        if not db_ok:
            status = "unhealthy"
        elif not redis_ok:
            status = "degraded"  # Working with in-memory fallback

        logs = [
            CrawlLogItem(
                id=i,
                crawler_type=l["type"],
                target_url=l["target"],
                status=l["status"],
                articles_found=l["found"],
                articles_new=l["new"],
                executed_at=l["time"],
            )
            for i, l in enumerate(stats["latest_logs"], 1)
        ]

        return CrawlerHealthResponse(
            status=status,
            database_connected=db_ok,
            redis_connected=redis_ok,
            deduplicator_type=dedup_type,
            total_categories=stats["total_categories"],
            total_articles=stats["total_articles"],
            total_media=stats["total_media"],
            seen_ids_count=seen_count,
            latest_logs=logs,
        )

    @staticmethod
    def execute_crawl_task(
        task_type: str,
        target: str,
        pages: int = 1,
        max_articles: Optional[int] = 10,
    ) -> None:
        """Run crawl pipeline asynchronously in background task."""
        logger.info("Executing background crawl task: type=%s, target=%s", task_type, target)
        pipeline = ArticlePipeline()
        try:
            if task_type == "rss":
                pipeline.crawl_rss(topic=target, max_articles=max_articles)
            elif task_type == "category":
                pipeline.crawl_category(category_slug=target, max_pages=pages, max_articles=max_articles)
            logger.info("Background crawl task completed for %s", target)
        except Exception as exc:
            logger.error("Background crawl task failed for %s: %s", target, exc)
