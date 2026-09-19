"""Pipeline to crawl article listings, deduplicate, fetch details, and store into DB."""

import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin

from crawler.config import settings
from crawler.deduplicator import Deduplicator, get_deduplicator
from crawler.http_client import HttpClient
from crawler.parsers.article import ArticleParser
from crawler.parsers.base import ParsedArticle
from crawler.parsers.listing import ListingParser
from crawler.parsers.rss import RSSParser
from crawler.storage.database import get_db_session
from crawler.storage.repository import Repository

logger = logging.getLogger(__name__)


class ArticlePipeline:
    """Manages the full lifecycle of fetching listings, deduplicating, parsing, and storing articles."""

    def __init__(
        self,
        http_client: Optional[HttpClient] = None,
        deduplicator: Optional[Deduplicator] = None,
    ):
        self.http_client = http_client or HttpClient()
        self.deduplicator = deduplicator or get_deduplicator()
        self.listing_parser = ListingParser(base_url=settings.base_url)
        self.article_parser = ArticleParser(base_url=settings.base_url)
        self.rss_parser = RSSParser()

    def crawl_category(
        self,
        category_slug: str,
        max_pages: int = 20,
        max_articles: Optional[int] = None,
    ) -> Dict[str, int]:
        """Crawl a category from page 1 up to max_pages (or until no more articles found)."""
        cat_url = urljoin(settings.base_url, "/" + category_slug.strip("/"))
        page_urls = self.listing_parser.generate_category_page_urls(cat_url, total_pages=max_pages)

        total_found = 0
        total_new = 0

        logger.info("Starting crawl for category '%s' across %d pages", category_slug, len(page_urls))

        with get_db_session() as session:
            repo = Repository(session)
            db_cat = repo.get_category_by_slug(category_slug)
            category_id = db_cat.id if db_cat else None

            for page_idx, page_url in enumerate(page_urls, start=1):
                if max_articles and total_new >= max_articles:
                    logger.info("Reached maximum requested articles limit: %d", max_articles)
                    break

                logger.info("Fetching listing page %d/%d: %s", page_idx, max_pages, page_url)
                try:
                    resp = self.http_client.fetch(page_url)
                    listing_items = self.listing_parser.parse_listing(resp.text, category_slug)
                    if not listing_items:
                        logger.info("No articles found on page %d. Stopping pagination.", page_idx)
                        break

                    total_found += len(listing_items)

                    # Deduplicate
                    all_ids = [item.id for item in listing_items]
                    unseen_ids = set(self.deduplicator.filter_unseen(all_ids))
                    logger.info(
                        "Page %d: Found %d articles (%d new, %d already seen)",
                        page_idx,
                        len(listing_items),
                        len(unseen_ids),
                        len(all_ids) - len(unseen_ids),
                    )

                    for item in listing_items:
                        if item.id not in unseen_ids:
                            continue

                        if max_articles and total_new >= max_articles:
                            break

                        # Fetch and parse article detail
                        success = self._fetch_and_save_article(
                            repo=repo,
                            url=item.url,
                            category_id=category_id,
                            fallback_title=item.title,
                            fallback_desc=item.description,
                            fallback_thumb=item.thumbnail_url,
                        )

                        if success:
                            self.deduplicator.mark_seen(item.id)
                            total_new += 1

                except Exception as exc:
                    logger.error("Error crawling page %s: %s", page_url, exc)
                    repo.log_crawl("listing", page_url, "failed", error_message=str(exc))
                    continue

            repo.log_crawl(
                "listing",
                cat_url,
                "success",
                articles_found=total_found,
                articles_new=total_new,
            )

        logger.info(
            "Crawl finished for '%s': %d articles found, %d newly ingested.",
            category_slug,
            total_found,
            total_new,
        )
        return {"articles_found": total_found, "articles_new": total_new}

    def crawl_rss(self, topic: str = "tin-moi-nhat", max_articles: Optional[int] = None) -> Dict[str, int]:
        """Fetch newest articles from VnExpress RSS feed."""
        if not topic.endswith(".rss"):
            rss_url = f"{settings.rss_base_url}/{topic}.rss"
        else:
            rss_url = f"{settings.rss_base_url}/{topic}"

        logger.info("Fetching RSS feed from: %s", rss_url)

        with get_db_session() as session:
            repo = Repository(session)
            try:
                resp = self.http_client.fetch(rss_url)
                rss_items = self.rss_parser.parse(resp.text)
            except Exception as exc:
                logger.error("Failed to fetch RSS feed: %s", exc)
                repo.log_crawl("rss", rss_url, "failed", error_message=str(exc))
                return {"articles_found": 0, "articles_new": 0}

            total_found = len(rss_items)
            valid_items = [it for it in rss_items if it.article_id is not None]
            unseen_ids = set(self.deduplicator.filter_unseen([it.article_id for it in valid_items]))

            logger.info("RSS feed: %d items found, %d unseen", total_found, len(unseen_ids))

            total_new = 0
            for item in valid_items:
                if item.article_id not in unseen_ids:
                    continue

                if max_articles and total_new >= max_articles:
                    break

                success = self._fetch_and_save_article(
                    repo=repo,
                    url=item.link,
                    fallback_title=item.title,
                    fallback_desc=item.description,
                    fallback_thumb=item.thumbnail_url,
                )

                if success:
                    self.deduplicator.mark_seen(item.article_id)
                    total_new += 1

            repo.log_crawl(
                "rss",
                rss_url,
                "success",
                articles_found=total_found,
                articles_new=total_new,
            )

        return {"articles_found": total_found, "articles_new": total_new}

    def crawl_single_article(self, url: str) -> Optional[ParsedArticle]:
        """Fetch, parse, and save a single article by URL."""
        with get_db_session() as session:
            repo = Repository(session)
            try:
                resp = self.http_client.fetch(url)
                parsed = self.article_parser.parse(resp.text, url)
                if not parsed:
                    return None

                cat_id = None
                if parsed.category_slug:
                    db_cat = repo.get_category_by_slug(parsed.category_slug)
                    if db_cat:
                        cat_id = db_cat.id

                art_dict = {
                    "id": parsed.id,
                    "title": parsed.title,
                    "slug": parsed.slug,
                    "description": parsed.description,
                    "content_html": parsed.content_html,
                    "content_text": parsed.content_text,
                    "author": parsed.author,
                    "thumbnail_url": parsed.thumbnail_url,
                    "origin_url": parsed.origin_url,
                    "category_id": cat_id,
                    "published_at": parsed.published_at,
                    "comment_count": parsed.comment_count,
                }
                media_dicts = [m.model_dump() for m in parsed.media]
                repo.upsert_article(art_dict, media_dicts)
                self.deduplicator.mark_seen(parsed.id)
                return parsed
            except Exception as exc:
                logger.error("Failed to crawl single article %s: %s", url, exc)
                return None

    def _fetch_and_save_article(
        self,
        repo: Repository,
        url: str,
        category_id: Optional[int] = None,
        fallback_title: Optional[str] = None,
        fallback_desc: Optional[str] = None,
        fallback_thumb: Optional[str] = None,
    ) -> bool:
        """Internal helper to fetch article detail, parse, and store."""
        try:
            resp = self.http_client.fetch(url)
            parsed = self.article_parser.parse(resp.text, url)
            if not parsed:
                logger.warning("Could not parse article detail: %s", url)
                return False

            # If category_id not provided, try to find category by slug
            if category_id is None and parsed.category_slug:
                db_cat = repo.get_category_by_slug(parsed.category_slug)
                if db_cat:
                    category_id = db_cat.id

            article_data = {
                "id": parsed.id,
                "title": parsed.title or fallback_title or "Không có tiêu đề",
                "slug": parsed.slug,
                "description": parsed.description or fallback_desc,
                "content_html": parsed.content_html,
                "content_text": parsed.content_text,
                "author": parsed.author,
                "thumbnail_url": parsed.thumbnail_url or fallback_thumb,
                "origin_url": parsed.origin_url,
                "category_id": category_id,
                "published_at": parsed.published_at,
                "comment_count": parsed.comment_count,
            }
            media_items = [m.model_dump() for m in parsed.media]

            repo.upsert_article(article_data, media_items)
            logger.info("Successfully ingested article [%d]: %s", parsed.id, parsed.title[:50])
            return True
        except Exception as exc:
            logger.error("Failed to fetch/save article %s: %s", url, exc)
            return False
