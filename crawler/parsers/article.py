"""Parser for VnExpress article detail pages (text articles, photo stories, and video news)."""

import copy
import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from crawler.config import settings
from crawler.parsers.base import (
    ParsedArticle,
    ParsedMedia,
    extract_article_id,
    extract_slug,
    parse_vnexpress_date,
)

logger = logging.getLogger(__name__)

# Elements to remove from content_html
JUNK_SELECTORS = [
    "script",
    "style",
    "iframe:not([src*='youtube']):not([src*='vnecdn'])",
    ".banner-ads",
    ".banner",
    ".box-tinlienquan",
    ".inner-article",
    ".box-vote",
    ".list_video_tin_lien_quan",
    ".header-content",
    ".social-share",
    ".footer-content",
    "#_large_1",
    "#_large_2",
    ".lazier",
    ".box-comment",
    "#box_comment_vne",
]


class ArticleParser:
    """Parser to extract full article content, metadata, clean HTML, and media items."""

    def __init__(self, base_url: str = settings.base_url):
        self.base_url = base_url

    def parse(self, html: str, url: str) -> Optional[ParsedArticle]:
        """Parse complete article details from HTML string."""
        soup = BeautifulSoup(html, "lxml")

        # 1. Article ID
        art_id = extract_article_id(url)
        if not art_id:
            # Fallback to meta tag or data-article-id
            id_meta = soup.find("meta", {"name": "tt_article_id"}) or soup.find("meta", {"property": "article:id"})
            if id_meta and id_meta.get("content", "").isdigit():
                art_id = int(id_meta["content"])
            else:
                logger.warning("Could not determine article ID for URL: %s", url)
                return None

        # 2. Title
        title_tag = soup.select_one("h1.title-detail") or soup.select_one("h1.title-news") or soup.find("h1")
        if not title_tag:
            logger.warning("No title found for URL: %s", url)
            return None
        title = title_tag.get_text(strip=True)

        # 3. Slug
        slug = extract_slug(url)

        # 4. Sapo / Description
        desc_tag = soup.select_one("p.description") or soup.find("meta", {"name": "description"})
        if isinstance(desc_tag, Tag) and desc_tag.name == "p":
            description = desc_tag.get_text(strip=True)
        elif isinstance(desc_tag, Tag) and desc_tag.has_attr("content"):
            description = desc_tag["content"].strip()
        else:
            description = None

        # 5. Published Date
        published_at = self._extract_publish_date(soup)

        # 6. Category / Breadcrumbs
        category_slug = self._extract_category_slug(soup, url)

        # 7. Content container: article.fck_detail (or main article body)
        content_container = soup.select_one("article.fck_detail") or soup.select_one(".content-detail")
        if not content_container:
            content_container = soup.select_one(".fck_detail")

        if not content_container:
            logger.warning("No article content container found for %s", url)
            return None

        # 8. Extract Media (Images & Videos) before mutating content_container
        media_list = self._extract_media(content_container)

        # 9. Extract Author
        author = self._extract_author(content_container)

        # 10. Clean HTML and text extraction
        clean_html, clean_text = self._clean_content(content_container)

        # 11. Main Thumbnail
        thumbnail_url = self._extract_main_thumbnail(soup, media_list)

        return ParsedArticle(
            id=art_id,
            title=title,
            slug=slug,
            description=description,
            content_html=clean_html,
            content_text=clean_text,
            author=author,
            thumbnail_url=thumbnail_url,
            origin_url=url,
            category_slug=category_slug,
            published_at=published_at,
            media=media_list,
        )

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        # Meta tags first
        meta_date = (
            soup.find("meta", {"name": "pubdate"})
            or soup.find("meta", {"property": "article:published_time"})
            or soup.find("meta", {"name": "its_publication"})
        )
        if meta_date and meta_date.get("content"):
            parsed = parse_vnexpress_date(meta_date["content"])
            if parsed:
                return parsed

        # In-page span.date
        date_span = soup.select_one("span.date")
        if date_span:
            return parse_vnexpress_date(date_span.get_text(strip=True))

        return None

    def _extract_category_slug(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        # Try breadcrumb
        breadcrumb = soup.select("ul.breadcrumb li a")
        if breadcrumb and len(breadcrumb) > 0:
            last_cat_a = breadcrumb[-1]
            href = last_cat_a.get("href", "")
            path = urlparse(href).path.strip("/")
            if path and path != "tin-tuc-24h":
                return path

        # Try parsing from URL path: vnexpress.net/<category>/<subcat>/slug-id.html
        path = urlparse(url).path.strip("/")
        parts = path.split("/")
        if len(parts) > 1:
            return "/".join(parts[:-1])
        return None

    def _extract_author(self, container: Tag) -> Optional[str]:
        # Often at end of article in p.Normal strong or p.author_mail / p[align="right"]
        author_tag = (
            container.select_one("p.author_mail")
            or container.select_one("p.author")
            or container.select_one("p[align='right'] strong")
            or container.select_one(".author")
        )
        if author_tag:
            return author_tag.get_text(strip=True)

        # Check last paragraph
        p_tags = container.find_all("p")
        if p_tags:
            last_p = p_tags[-1]
            strong = last_p.find("strong")
            if strong and len(strong.get_text(strip=True)) < 60:
                return strong.get_text(strip=True)

        return None

    def _extract_media(self, container: Tag) -> List[ParsedMedia]:
        import html as html_lib
        media_list: List[ParsedMedia] = []
        seen_urls = set()

        # 1. Extract Gallery items (common in photo stories / albums across all categories)
        for g_item in container.select(".item_gallery_new, .gallery_block .item_gallery"):
            g_img = g_item.find("img")
            img_url = (
                (g_img.get("data-desktop-src") or g_img.get("data-src") or g_img.get("src"))
                if g_img
                else (g_item.get("data-component-value1") or g_item.get("data-src"))
            )
            if img_url and not img_url.startswith("data:") and img_url not in seen_urls:
                seen_urls.add(img_url)
                caption = None
                if g_img and g_img.get("data-caption"):
                    raw_cap = html_lib.unescape(g_img["data-caption"])
                    cap_soup = BeautifulSoup(raw_cap, "html.parser")
                    caption = cap_soup.get_text(strip=True)

                if not caption:
                    cap_div = g_item.find_next_sibling(class_=re.compile(r"caption[-_]gallery|desc_cation"))
                    if cap_div:
                        caption = cap_div.get_text(strip=True)

                media_list.append(
                    ParsedMedia(
                        type="image",
                        url=img_url,
                        caption=caption or None,
                    )
                )

        # 2. Extract Figures and standard images
        for fig in container.find_all("figure"):
            img = fig.find("img")
            if not img:
                continue

            img_url = (
                img.get("data-desktop-src")
                or img.get("data-src")
                or img.get("src")
            )
            if not img_url or img_url.startswith("data:") or img_url in seen_urls:
                continue

            seen_urls.add(img_url)

            # Caption: figcaption, desc_cation, caption-gallery, or data-caption
            caption = None
            figcaption = fig.find("figcaption")
            if figcaption:
                caption = figcaption.get_text(strip=True)
            elif fig.select_one(".caption-gallery, .desc_cation, .caption"):
                caption = fig.select_one(".caption-gallery, .desc_cation, .caption").get_text(strip=True)
            elif img.get("data-caption"):
                raw_cap = html_lib.unescape(img["data-caption"])
                cap_soup = BeautifulSoup(raw_cap, "html.parser")
                caption = cap_soup.get_text(strip=True)
            elif img.get("alt"):
                caption = img["alt"].strip()

            width = int(img["width"]) if img.has_attr("width") and img["width"].isdigit() else None
            height = int(img["height"]) if img.has_attr("height") and img["height"].isdigit() else None

            media_list.append(
                ParsedMedia(
                    type="image",
                    url=img_url,
                    caption=caption or None,
                    width=width,
                    height=height,
                )
            )

        # 3. In case images were not inside figure or gallery tags
        for img in container.find_all("img"):
            img_url = img.get("data-desktop-src") or img.get("data-src") or img.get("src")
            if not img_url or img_url.startswith("data:") or img_url in seen_urls:
                continue
            seen_urls.add(img_url)
            caption = None
            if img.get("data-caption"):
                raw_cap = html_lib.unescape(img["data-caption"])
                cap_soup = BeautifulSoup(raw_cap, "html.parser")
                caption = cap_soup.get_text(strip=True)
            else:
                caption = img.get("alt")

            media_list.append(
                ParsedMedia(
                    type="image",
                    url=img_url,
                    caption=caption or None,
                )
            )

        # 4. Extract embedded videos inside article body
        for v_el in container.select("video, [data-video], [data-component-type='video']"):
            video_url = (
                v_el.get("data-video")
                or v_el.get("src")
                or (v_el.find("source").get("src") if v_el.find("source") else None)
            )
            if video_url and video_url not in seen_urls and not video_url.startswith("data:"):
                seen_urls.add(video_url)
                v_cap = v_el.get("title") or (v_el.find_parent("figure").find("figcaption").get_text(strip=True) if v_el.find_parent("figure") and v_el.find_parent("figure").find("figcaption") else None)
                media_list.append(
                    ParsedMedia(
                        type="video",
                        url=video_url,
                        caption=v_cap or None,
                    )
                )

        # 5. Extract audio / podcast inside article body
        for a_el in container.select("audio, [data-audio], [data-component-type='audio']"):
            audio_url = (
                a_el.get("data-audio")
                or a_el.get("src")
                or (a_el.find("source").get("src") if a_el.find("source") else None)
            )
            if audio_url and audio_url not in seen_urls and not audio_url.startswith("data:"):
                seen_urls.add(audio_url)
                media_list.append(
                    ParsedMedia(
                        type="audio",
                        url=audio_url,
                        caption=a_el.get("title") or "Audio Podcast",
                    )
                )

        return media_list

    def _extract_main_thumbnail(self, soup: BeautifulSoup, media_list: List[ParsedMedia]) -> Optional[str]:
        # Check og:image meta tag
        og_img = soup.find("meta", {"property": "og:image"})
        if og_img and og_img.get("content") and not og_img["content"].endswith("logo.png"):
            return og_img["content"]

        # Use first image from article media
        if media_list:
            return media_list[0].url

        return None

    def _clean_content(self, container: Tag) -> (str, str):
        """Strip junk elements, sanitize images, and return (clean_html, clean_text)."""
        content_copy = copy.copy(container)

        # Decompose junk selectors
        for selector in JUNK_SELECTORS:
            for el in content_copy.select(selector):
                el.decompose()

        # Sanitize images: ensure src is pointing to data-src if present
        for img in content_copy.find_all("img"):
            actual_src = img.get("data-src") or img.get("src")
            if actual_src:
                img["src"] = actual_src
            if img.has_attr("data-src"):
                del img["data-src"]
            if img.has_attr("loading"):
                del img["loading"]

        # Strip unneeded wrapper divs if empty
        clean_html = str(content_copy).strip()

        # Extract plain text
        clean_text = content_copy.get_text(separator="\n", strip=True)
        # Normalize excessive newlines
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

        return clean_html, clean_text
