"""Parser for VnExpress RSS feeds."""

import logging
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Optional
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from crawler.parsers.base import ParsedRSSItem, extract_article_id

logger = logging.getLogger(__name__)


class RSSParser:
    """Parser for RSS 2.0 XML feeds from VnExpress."""

    def parse(self, xml_content: str) -> List[ParsedRSSItem]:
        """Parse RSS XML into a list of ParsedRSSItem."""
        items: List[ParsedRSSItem] = []

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            logger.error("XML parse error: %s. Trying BeautifulSoup xml parser...", exc)
            return self._parse_with_soup(xml_content)

        channel = root.find("channel")
        if channel is None:
            logger.warning("No channel element found in RSS")
            return []

        for item_node in channel.findall("item"):
            title = (item_node.findtext("title") or "").strip()
            link = (item_node.findtext("link") or "").strip()
            raw_desc = item_node.findtext("description") or ""
            pub_date_str = item_node.findtext("pubDate") or ""
            guid = item_node.findtext("guid")

            clean_desc, thumb_url = self._extract_desc_and_thumb(raw_desc)
            pub_date = self._parse_rss_date(pub_date_str)
            art_id = extract_article_id(link)

            # Also check enclosure tag for thumbnail
            enclosure = item_node.find("enclosure")
            if enclosure is not None and not thumb_url:
                thumb_url = enclosure.get("url")

            items.append(
                ParsedRSSItem(
                    title=title,
                    link=link,
                    description=clean_desc,
                    pub_date=pub_date,
                    guid=guid,
                    thumbnail_url=thumb_url,
                    article_id=art_id,
                )
            )

        return items

    def _parse_with_soup(self, xml_content: str) -> List[ParsedRSSItem]:
        soup = BeautifulSoup(xml_content, "xml")
        items: List[ParsedRSSItem] = []
        for item_node in soup.find_all("item"):
            title = item_node.find("title")
            link = item_node.find("link")
            desc = item_node.find("description")
            pub_date = item_node.find("pubDate")
            guid = item_node.find("guid")

            title_str = title.get_text(strip=True) if title else ""
            link_str = link.get_text(strip=True) if link else ""
            raw_desc = desc.get_text(strip=True) if desc else ""
            pub_date_str = pub_date.get_text(strip=True) if pub_date else ""
            guid_str = guid.get_text(strip=True) if guid else None

            clean_desc, thumb_url = self._extract_desc_and_thumb(raw_desc)
            parsed_date = self._parse_rss_date(pub_date_str)
            art_id = extract_article_id(link_str)

            items.append(
                ParsedRSSItem(
                    title=title_str,
                    link=link_str,
                    description=clean_desc,
                    pub_date=parsed_date,
                    guid=guid_str,
                    thumbnail_url=thumb_url,
                    article_id=art_id,
                )
            )
        return items

    def _extract_desc_and_thumb(self, raw_desc: str) -> (Optional[str], Optional[str]):
        if not raw_desc:
            return None, None

        soup = BeautifulSoup(raw_desc, "html.parser")
        img = soup.find("img")
        thumb_url = img.get("src") if img else None

        # Remove <a> and <img> from description
        for tag in soup.find_all(["a", "img"]):
            tag.decompose()

        clean_text = soup.get_text(strip=True)
        return clean_text or None, thumb_url

    def _parse_rss_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return None
