"""Parser for category listing pages (Page 1 multi-container and Page 2-20)."""

import copy
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
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

        # Find all article containers (article, section, or div with item-news/article-item/article-topstory)
        article_tags = soup.find_all(
            lambda tag: tag.name in ("article", "section", "div")
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
        title_tag = (
            tag.select_one(".title-news a")
            or tag.select_one("h1 a, h2 a, h3 a, h4 a")
            or tag.select_one(".inner-title")
        )
        thumb_a = tag.select_one(".thumb-art a, a.thumb")

        href = ""
        title = ""

        if title_tag:
            href = title_tag.get("href", "").strip()
            # Clean span.nb-art, icon-cat, badges to prevent title pollution (e.g. 1Sống lại...)
            t_copy = copy.copy(title_tag)
            for badge in t_copy.select(".nb-art, .icon-cat, .badge, svg"):
                badge.decompose()
            title = t_copy.get_text(strip=True)

        if thumb_a:
            thumb_href = thumb_a.get("href", "").strip()
            # If thumb links to author profile or tag, ignore it for article href
            if not href and thumb_href and "/tac-gia/" not in thumb_href and "/tag/" not in thumb_href:
                href = thumb_href
            if not title:
                title = thumb_a.get("title", "").strip()

        if not href:
            return None

        art_id = extract_article_id(href)
        # Fallback to data-ea-aid or data-aid on article tag
        if not art_id:
            aid_attr = tag.get("data-ea-aid") or tag.get("data-aid")
            if aid_attr and aid_attr.isdigit():
                art_id = int(aid_attr)

        if not art_id:
            return None

        full_url = urljoin(self.base_url, href)

        # 2. Extract description (sapo) and comment count
        comment_count = 0
        cmt_tag = (
            tag.select_one(".meta-news .count_cmt span")
            or tag.select_one(".count_cmt [class*='widget-comment']")
            or tag.select_one(".count_cmt span")
            or tag.select_one(".meta-news .font_icon")
            or tag.select_one(".count_cmt")
            or tag.select_one("[class*='widget-comment']")
        )
        if cmt_tag:
            digits = re.sub(r"[^\d]", "", cmt_tag.get_text(strip=True))
            if digits:
                comment_count = int(digits)

        description = None
        desc_tag = tag.select_one("p.description")
        if desc_tag:
            # Remove any meta-news or comment sub-elements inside p.description
            for sub in desc_tag.select(".meta-news, .count_cmt, script, style"):
                sub.decompose()
            description = desc_tag.get_text(strip=True)

        # 3. Extract thumbnail (Image or Video preview/poster)
        thumbnail_url = None
        img_tag = tag.select_one("picture img, .thumb-art img, img")
        if img_tag:
            thumbnail_url = (
                img_tag.get("data-desktop-src")
                or img_tag.get("data-src")
                or img_tag.get("src")
                or img_tag.get("data-ll-status")
            )
            # Sometimes src is lazy placeholder, check srcset
            source_tag = tag.select_one("picture source")
            if source_tag and source_tag.get("srcset"):
                srcset = source_tag["srcset"].split(",")[0].strip().split(" ")[0]
                if srcset and not srcset.startswith("data:"):
                    thumbnail_url = srcset

        # If no image thumbnail, check for video preview / poster (common in Thoi su / Video news)
        if not thumbnail_url or thumbnail_url.startswith("data:"):
            video_tag = tag.select_one("video")
            if video_tag:
                thumbnail_url = (
                    video_tag.get("poster")
                    or (video_tag.find("source").get("data-src-image") if video_tag.find("source") else None)
                    or video_tag.get("src")
                )

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
            comment_count=comment_count,
        )

    def extract_pagination(self, html: str) -> List[str]:
        """Extract pagination page links found in the HTML."""
        soup = BeautifulSoup(html, "lxml")
        paging = (
            soup.select_one("div#pagination")
            or soup.select_one("div.paging")
            or soup.select_one("div.pagination")
            or soup.select_one("ul.pagination")
            or soup.select_one("nav.pagination")
        )
        links = []
        if paging:
            for a in paging.find_all("a", href=True):
                href = a["href"].strip()
                if href and not href.startswith("javascript:") and not href.startswith("#"):
                    links.append(urljoin(self.base_url, href))

        for btn in soup.select("a.btn-page[href], a.pagination__next[href]"):
            href = btn.get("href", "").strip()
            if href and not href.startswith("javascript:") and not href.startswith("#"):
                links.append(urljoin(self.base_url, href))

        return list(dict.fromkeys(links))

    def extract_ajax_paging(self, html: str) -> Optional[Dict[str, Any]]:
        """Extract AJAX pagination parameters if present (e.g. from div#paging, [data-container='paging'], [data-url*='ajax'])."""
        soup = BeautifulSoup(html, "lxml")
        paging = (
            soup.select_one("div#paging[data-url]")
            or soup.select_one("[data-container='paging'][data-url]")
            or soup.select_one("[data-url*='/ajax/']")
            or soup.select_one("[data-url]")
        )
        if paging and paging.get("data-url"):
            data_url = paging.get("data-url", "").strip()
            if "/ajax/" in data_url or "ajax" in data_url:
                data_page = paging.get("data-page", 2)
                page_num = int(data_page) if str(data_page).isdigit() else 2
                return {
                    "url": data_url,
                    "category_id": paging.get("data-category") or paging.get("data-cate-id") or paging.get("data-cate"),
                    "page": page_num,
                    "exclude": paging.get("data-exclude", ""),
                }
        return None

    def build_ajax_page_url(self, ajax_info: Dict[str, Any], page_num: int) -> str:
        """Build full AJAX endpoint URL with query parameters for a specific page."""
        raw_url = ajax_info["url"]
        full_url = urljoin(self.base_url, raw_url)
        params = []
        if ajax_info.get("category_id"):
            params.append(f"category_id={ajax_info['category_id']}")
        params.append(f"page={page_num}")
        if ajax_info.get("exclude"):
            params.append(f"exclude={ajax_info['exclude']}")
        sep = "&" if "?" in full_url else "?"
        return f"{full_url}{sep}{'&'.join(params)}"

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
