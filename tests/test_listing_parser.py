"""Unit tests for ListingParser using sample HTML files from docs/."""

from pathlib import Path
import pytest

from crawler.parsers.listing import ListingParser


DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


@pytest.fixture
def parser():
    return ListingParser(base_url="https://vnexpress.net")


def test_parse_listing_page2_20(parser):
    """Test extracting articles and pagination from news-container-page2-20.html."""
    html_file = DOCS_DIR / "news-container-page2-20.html"
    assert html_file.exists(), f"Sample file not found at {html_file}"

    html_content = html_file.read_text(encoding="utf-8")
    items = parser.parse_listing(html_content, category_slug="khoa-hoc-cong-nghe")

    assert len(items) > 0, "Should extract at least one article"

    # Verify topstory article: "Nhà mạng Việt Nam tắt hoàn toàn sóng 2G từ 15/9" (ID 5120434)
    item_5120434 = next((item for item in items if item.id == 5120434), None)
    assert item_5120434 is not None
    assert "Nhà mạng Việt Nam tắt hoàn toàn sóng 2G" in item_5120434.title
    assert "https://vnexpress.net/nha-mang-viet-nam-tat-hoan-toan-song-2g-tu-15-9-5120434.html" == item_5120434.url
    assert item_5120434.description is not None
    assert "Mạng 2G chính thức ngừng hoạt động" in item_5120434.description
    assert item_5120434.thumbnail_url is not None
    assert "webp" in item_5120434.thumbnail_url or "jpg" in item_5120434.thumbnail_url

    # Check pagination extraction
    pagination_links = parser.extract_pagination(html_content)
    assert len(pagination_links) > 0
    assert any("/khoa-hoc-cong-nghe-p3" in link for link in pagination_links)


def test_parse_listing_container_top_header(parser):
    """Test extracting articles from container-top-header.html / news-container01.html."""
    html_file = DOCS_DIR / "container-top-header.html"
    assert html_file.exists()

    html_content = html_file.read_text(encoding="utf-8")
    items = parser.parse_listing(html_content, category_slug="khoa-hoc-cong-nghe")

    assert len(items) >= 4  # 1 topstory + 3 grid articles

    # Topstory: Gemini (5122237)
    item_gemini = next((item for item in items if item.id == 5122237), None)
    assert item_gemini is not None
    assert "Gemini tấn công mạng" in item_gemini.title
    assert "Google thừa nhận" in item_gemini.description

    # Sub items
    item_claude = next((item for item in items if item.id == 5121950), None)
    assert item_claude is not None
    assert "AI Claude tham gia phát triển" in item_claude.title


def test_parse_listing_container02(parser):
    """Test extracting articles from news-container02.html."""
    html_file = DOCS_DIR / "news-container02.html"
    assert html_file.exists()

    html_content = html_file.read_text(encoding="utf-8")
    items = parser.parse_listing(html_content, category_slug="khoa-hoc-cong-nghe")

    assert len(items) > 0
    # Check iPhone 18 Pro Max article (5122052)
    item_iphone = next((item for item in items if item.id == 5122052), None)
    assert item_iphone is not None
    assert "Tháo rời" in item_iphone.title or "iPhone" in item_iphone.title


def test_generate_category_page_urls():
    """Test pagination URL generator for 20 pages."""
    urls = ListingParser.generate_category_page_urls("https://vnexpress.net/khoa-hoc-cong-nghe", total_pages=5)
    assert len(urls) == 5
    assert urls[0] == "https://vnexpress.net/khoa-hoc-cong-nghe"
    assert urls[1] == "https://vnexpress.net/khoa-hoc-cong-nghe-p2"
    assert urls[4] == "https://vnexpress.net/khoa-hoc-cong-nghe-p5"


def test_parse_listing_content_thoi_su_example(parser):
    """Test extracting articles from content-thoi-su-example.html."""
    html_file = DOCS_DIR / "content-thoi-su-example.html"
    assert html_file.exists()

    html_content = html_file.read_text(encoding="utf-8")
    items = parser.parse_listing(html_content, category_slug="thoi-su")

    # Verify article count (58 unique articles)
    assert len(items) >= 55

    # 1. Topstory article: Vinh mưa kỷ lục (5122322)
    item_vinh = next((item for item in items if item.id == 5122322), None)
    assert item_vinh is not None
    assert "Vinh hứng trận mưa kỷ lục" in item_vinh.title
    assert item_vinh.thumbnail_url is not None

    # 2. Video thumbnail article: Quy hoạch sông Hồng (5120741)
    item_video = next((item for item in items if item.id == 5120741), None)
    assert item_video is not None
    assert "Quy hoạch sông Hồng" in item_video.title
    assert item_video.thumbnail_url is not None
    assert "settop2" in item_video.thumbnail_url

    # 3. Tong-thuat / Live report article: Hà Nội mưa trên 150 mm (5121155)
    item_tongthuat = next((item for item in items if item.id == 5121155), None)
    assert item_tongthuat is not None
    assert "Hà Nội mưa trên 150 mm" in item_tongthuat.title
    assert "-5121155-tong-thuat.html" in item_tongthuat.url

