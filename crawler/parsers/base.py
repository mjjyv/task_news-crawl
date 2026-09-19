"""Base parser classes, Pydantic schemas, and parsing helpers."""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field


class ParsedCategory(BaseModel):
    name: str
    slug: str
    origin_url: str
    parent_slug: Optional[str] = None
    description: Optional[str] = None


class ParsedListingItem(BaseModel):
    id: int
    url: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    category_slug: Optional[str] = None
    comment_count: int = 0


class ParsedMedia(BaseModel):
    type: str = "image"  # 'image', 'video'
    url: str
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ParsedArticle(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str] = None
    content_html: str
    content_text: str
    author: Optional[str] = None
    thumbnail_url: Optional[str] = None
    origin_url: str
    category_slug: Optional[str] = None
    published_at: Optional[datetime] = None
    comment_count: int = 0
    media: List[ParsedMedia] = Field(default_factory=list)


class ParsedRSSItem(BaseModel):
    title: str
    link: str
    description: Optional[str] = None
    pub_date: Optional[datetime] = None
    guid: Optional[str] = None
    thumbnail_url: Optional[str] = None
    article_id: Optional[int] = None


def extract_article_id(url: str) -> Optional[int]:
    """Extract numeric article ID from VnExpress URL (supports standard, tong-thuat, p2, etc.)."""
    if not url:
        return None

    # Exclude author and tag pages
    if "/tac-gia/" in url or "/tag/" in url:
        return None

    # Match: -<id>.html or -<id>-<suffix>.html where suffix is tong-thuat, p2, video, etc.
    match = re.search(r"-(\d+)(?:-(?:tong-thuat|p\d+|video|preview|box))?\.html(?:[?#].*)?$", url)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def extract_slug(url: str) -> str:
    """Extract clean article or category slug from URL."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if path.endswith(".html"):
        filename = path[:-5]
        # Remove trailing known suffix if present
        filename = re.sub(r"-(?:tong-thuat|p\d+|video|preview|box)$", "", filename)
        # Remove trailing ID
        parts = filename.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0]
        return filename
    # Category slug: /khoa-hoc-cong-nghe/ai -> khoa-hoc-cong-nghe/ai
    return path


def parse_vnexpress_date(date_str: str) -> Optional[datetime]:
    """Parse various VnExpress date formats into UTC datetime."""
    if not date_str:
        return None

    date_str = date_str.strip()

    # ISO format: 2026-09-17T07:31:00+07:00 or 2026-09-19 18:00:00
    try:
        if "T" in date_str:
            return datetime.fromisoformat(date_str)
        if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", date_str):
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    # Standard VnExpress text format: "Thứ năm, 17/9/2026, 07:31 (GMT+7)"
    # or "17/9/2026, 07:31 (GMT+7)"
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4}),?\s+(\d{1,2}):(\d{2})", date_str)
    if m:
        day, month, year, hour, minute = map(int, m.groups())
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            pass

    return None
