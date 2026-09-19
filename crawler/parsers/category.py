"""Parser for VnExpress main categories and subcategories."""

import logging
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from crawler.config import settings
from crawler.parsers.base import ParsedCategory, extract_slug

logger = logging.getLogger(__name__)

# Excluded slugs from top menu that are not news categories
EXCLUDED_SLUGS = {
    "",
    "/",
    "tin-tuc-24h",
    "vne-go",
    "javascript:;",
    "#",
}


class CategoryParser:
    """Parser to discover and extract top-level and subcategories."""

    def __init__(self, base_url: str = settings.base_url):
        self.base_url = base_url

    def parse_main_categories(self, html: str) -> List[ParsedCategory]:
        """Parse top-level navigation categories from homepage or category header."""
        soup = BeautifulSoup(html, "lxml")
        categories: List[ParsedCategory] = []
        seen_slugs = set()

        # Find navigation list: ul.parent or nav#main-nav
        nav_ul = soup.select_one("ul.parent") or soup.select_one("nav#main-nav ul")
        if not nav_ul:
            logger.warning("Could not find top-level navigation container.")
            return []

        for li in nav_ul.find_all("li", recursive=False):
            a_tag = li.find("a", href=True)
            if not a_tag:
                continue

            href = a_tag["href"].strip()
            name = a_tag.get_text(strip=True)

            if not name or href.startswith("javascript:") or href.startswith("#"):
                continue

            # Normalized slug
            path = urlparse(href).path.strip("/")
            if not path or path in EXCLUDED_SLUGS:
                continue

            full_url = urljoin(self.base_url, "/" + path)
            if path in seen_slugs:
                continue
            seen_slugs.add(path)

            categories.append(
                ParsedCategory(
                    name=name,
                    slug=path,
                    origin_url=full_url,
                    parent_slug=None,
                )
            )

        return categories

    def parse_sub_categories(self, html: str, parent_slug: str) -> List[ParsedCategory]:
        """Parse subcategories from a category landing page."""
        soup = BeautifulSoup(html, "lxml")
        sub_categories: List[ParsedCategory] = []
        seen_slugs = set()

        # Check subnav: ul.ul-nav-folder or nav.folder or div.sub-menu
        folder_ul = (
            soup.select_one("ul.ul-nav-folder")
            or soup.select_one("nav.folder ul")
            or soup.select_one("div.sub-menu ul")
        )

        if not folder_ul:
            logger.debug("No sub-category navigation found for %s", parent_slug)
            return []

        for a_tag in folder_ul.find_all("a", href=True):
            href = a_tag["href"].strip()
            name = a_tag.get_text(strip=True)

            if not name or href.startswith("javascript:") or href.startswith("#"):
                continue

            path = urlparse(href).path.strip("/")
            if not path or path == parent_slug or path in seen_slugs:
                continue

            # Ensure subcategory slug starts with parent_slug or belongs to it
            full_url = urljoin(self.base_url, "/" + path)
            seen_slugs.add(path)

            sub_categories.append(
                ParsedCategory(
                    name=name,
                    slug=path,
                    origin_url=full_url,
                    parent_slug=parent_slug,
                )
            )

        return sub_categories
