"""Pipeline to discover and synchronize VnExpress categories and subcategories into DB."""

import logging
from typing import Dict, List, Optional

from crawler.config import settings
from crawler.http_client import HttpClient
from crawler.parsers.category import CategoryParser
from crawler.storage.database import get_db_session
from crawler.storage.repository import Repository

logger = logging.getLogger(__name__)


class CategorySyncPipeline:
    """Synchronizes main categories and subcategories into the database."""

    def __init__(self, http_client: Optional[HttpClient] = None):
        self.http_client = http_client or HttpClient()
        self.parser = CategoryParser(base_url=settings.base_url)

    def sync_all(self) -> Dict[str, int]:
        """Fetch homepage and category landing pages to populate all categories."""
        logger.info("Starting category synchronization from %s", settings.base_url)

        with get_db_session() as session:
            repo = Repository(session)

            # 1. Fetch homepage
            try:
                resp = self.http_client.fetch(settings.base_url)
                main_cats = self.parser.parse_main_categories(resp.text)
                logger.info("Discovered %d top-level categories", len(main_cats))
            except Exception as exc:
                logger.error("Failed to fetch homepage for categories: %s", exc)
                repo.log_crawl("category_sync", settings.base_url, "failed", error_message=str(exc))
                return {"parent_categories": 0, "sub_categories": 0}

            parent_count = 0
            sub_count = 0

            # 2. Save top-level categories and fetch their subcategories
            for p_cat in main_cats:
                parent_obj = repo.upsert_category(
                    name=p_cat.name,
                    slug=p_cat.slug,
                    origin_url=p_cat.origin_url,
                    parent_id=None,
                )
                parent_count += 1

                # Fetch category landing page for subcategories
                try:
                    logger.debug("Checking subcategories for: %s", p_cat.origin_url)
                    cat_resp = self.http_client.fetch(p_cat.origin_url)
                    sub_cats = self.parser.parse_sub_categories(cat_resp.text, p_cat.slug)

                    for s_cat in sub_cats:
                        repo.upsert_category(
                            name=s_cat.name,
                            slug=s_cat.slug,
                            origin_url=s_cat.origin_url,
                            parent_id=parent_obj.id,
                        )
                        sub_count += 1
                except Exception as sub_exc:
                    logger.warning("Failed to fetch subcategories for %s: %s", p_cat.slug, sub_exc)

            repo.log_crawl(
                "category_sync",
                settings.base_url,
                "success",
                articles_found=parent_count + sub_count,
                articles_new=parent_count + sub_count,
            )

        logger.info(
            "Category sync completed: %d parent categories, %d subcategories synced.",
            parent_count,
            sub_count,
        )
        return {"parent_categories": parent_count, "sub_categories": sub_count}
