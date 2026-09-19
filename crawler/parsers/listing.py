"""Parser for category listing pages (Page 1 multi-container and Page 2-20)."""

import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from crawler.config import settings
from crawler.parsers.base import (
    ParsedListingItem,
    extract_article_id,
    extract_slug,
    parse_vnexpress_date,
)

logger = logging.getLogger(__name__)


class ListingParser:
    """Extracts article links, metadata, and pagination from category listing HTML."""

    def __init__(self, base_url: str = settings.base_url):
        self.base_url = base_url

    def parse_listing(self, html: str, category_slug: Optional[str] = None) -> List[ParsedListingItem]:
        """Parse all articles from listing HTML (supports container01-04 and page2-20)."""
        soup = BeautifulSoup(html, "lxml")
        items: List[ParsedListingItem] = []
        seen_ids = set()

        # Find all article containers
        article_tags = soup.find_all(
            lambda tag: tag.name == "article"
            and (
                "item-news" in tag.get("class", [])
                or "article-item" in tag.get("class", [])
                or "article-topstory" in tag.get("class", [])
            )
        )

        for tag in article_tags:
            item = self._parse_article_tag(tag, category_slug)
            if item and item.id not in seen_ids:
                seen_ids.add(item.id)
                items.append(item)

        # Fallback: if structure was non-standard, find any link matching -(\d+)\.html in title containers
        if not items:
            title_links = soup.select(".title-news a, h2 a, h3 a, h4 a")
            for a in title_links:
                href = a.get("href", "")
                art_id = extract_article_id(href)
                title = a.get_text(strip=True)
                if art_id and title and art_id not in seen_ids:
                    full_url = urljoin(self.base_url, href)
                    seen_ids.add(art_id)
                    items.append(
                        ParsedListingItem(
                            id=art_id,
                            url=full_url,
                            title=title,
                            category_slug=category_slug,
                        )
                    )

        logger.debug("Extracted %d articles from listing HTML", len(items))
        return items

    def _parse_article_tag(self, tag: Tag, category_slug: Optional[str]) -> Optional[ParsedListingItem]:
        # 1. Extract link and title
        title_tag = tag.select_one(".title-news a") or tag.select_one("h1 a, h2 a, h3 a, h4 a")
        thumb_a = tag.select_one(".thumb-art a")

        href = ""
        title = ""

        if title_tag:
            href = title_tag.get("href", "").strip()
            title = title_tag.get_text(strip=True)

        if (not href or not title) and thumb_a:
            href = href or thumb_a.get("href", "").strip()
            title = title or thumb_a.get("title", "").strip()

        if not href:
            return None

        art_id = extract_article_id(href)
        if not art_id:
            return None

        full_url = urljoin(self.base_url, href)

        # 2. Extract description (sapo)
        description = None
        desc_tag = tag.select_one("p.description")
        if desc_tag:
            # Remove any meta-news or comment sub-elements inside p.description
            for sub in desc_tag.select(".meta-news, .count_cmt, script, style"):
                sub.decompose()
            description = desc_tag.get_text(strip=True)

        # 3. Extract thumbnail
        thumbnail_url = None
        img_tag = tag.select_one("picture img, .thumb-art img")
        if img_tag:
            thumbnail_url = (
                img_tag.get("data-src")
                or img_tag.get("src")
                or img_tag.get("data-ll-status")
            )
            # Sometimes src is lazy placeholder, check srcset
            source_tag = tag.select_one("picture source")
            if source_tag and source_tag.get("srcset"):
                # Take first url from srcset
                srcset = source_tag["srcset"].split(",")[0].strip().split(" ")[0]
                if srcset and not srcset.startswith("data:"):
                    thumbnail_url = srcset

        # 4. Extract publication date if present
        published_at = None
        time_tag = tag.select_one(".time-public [datetime]") or tag.select_one("[datetime]")
        if time_tag and time_tag.get("datetime"):
            published_at = parse_vnexpress_date(time_tag["datetime"])

        return ParsedListingItem(
            id=art_id,
            url=full_url,
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            published_at=published_at,
            category_slug=category_slug,
        )

    def extract_pagination(self, html: str) -> List[str]:
        """Extract pagination page links found in the HTML."""
        soup = BeautifulSoup(html, "lxml")
        paging = soup.select_one("div#pagination, div.paging")
        if not paging:
            return []

        links = []
        for a in paging.find_all("a", href=True):
            href = a["href"].strip()
            if href and not href.startswith("javascript:") and not href.startswith("#"):
                links.append(urljoin(self.base_url, href))
        return list(dict.fromkeys(links))

    @staticmethod
    def generate_category_page_urls(category_url: str, total_pages: int = 20) -> List[str]:
        """Generate page URLs from page 1 to total_pages (-p2 to -p20)."""
        base = category_url.rstrip("/")
        # If already ends with -p\d+, strip it
        base = re.sub(r"-p\d+$", "", base)

        urls = [base]  # Page 1
        for p in range(2, total_pages + 1):
            urls.append(f"{base}-p{p}")
        return urls
