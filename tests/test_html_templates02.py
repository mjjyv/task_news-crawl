"""Unit tests for HTML templates 02 (Goc Nhin AJAX pagination, Infographics/Photo stories, Comments, and Related Articles)."""

from pathlib import Path
import pytest

from crawler.parsers.article import ArticleParser
from crawler.parsers.listing import ListingParser

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "docs" / "html-templates02"


@pytest.fixture
def listing_parser():
    return ListingParser(base_url="https://vnexpress.net")


@pytest.fixture
def article_parser():
    return ArticleParser(base_url="https://vnexpress.net")


def test_parse_goc_nhin_listing(listing_parser):
    """Test parsing Goc Nhin container: clean titles without nb-art, correct URLs, and AJAX paging."""
    html_file = TEMPLATES_DIR / "goc-nhin_news-container.html"
    assert html_file.exists(), f"File not found: {html_file}"

    html_content = html_file.read_text(encoding="utf-8")
    items = listing_parser.parse_listing(html_content, category_slug="goc-nhin")

    assert len(items) == 51, f"Expected 51 articles, got {len(items)}"

    # 1. Verify clean title (nb-art badge "1", "2" stripped)
    item_5113898 = next((it for it in items if it.id == 5113898), None)
    assert item_5113898 is not None
    assert item_5113898.title == "Sống lại để 'được chết'", f"Title polluted: {item_5113898.title}"
    assert "https://vnexpress.net/song-lai-de-duoc-chet-5113898.html" == item_5113898.url

    item_5118083 = next((it for it in items if it.id == 5118083), None)
    assert item_5118083 is not None
    assert item_5118083.title == "'Khải hoàn môn' ở Hồ Gươm", f"Title polluted: {item_5118083.title}"

    # 2. Verify author link in thumb-art did not corrupt article URL
    item_top = next((it for it in items if it.id == 5123983), None)
    assert item_top is not None
    assert item_top.title == "Tội phạm và hình phạt"
    assert "https://vnexpress.net/toi-pham-va-hinh-phat-5123983.html" == item_top.url
    assert "/tac-gia/" not in item_top.url

    # 3. Verify AJAX pagination extraction
    ajax_paging = listing_parser.extract_ajax_paging(html_content)
    assert ajax_paging is not None
    assert ajax_paging["url"] == "/ajax/goc-nhin"
    assert ajax_paging["category_id"] == "1003450"
    assert ajax_paging["page"] == 2
    assert ajax_paging["exclude"] == "3"


def test_parse_goc_nhin_subcat_listing(listing_parser):
    """Test parsing Goc Nhin subcategory container (Chinh tri - chinh sach)."""
    html_file = TEMPLATES_DIR / "goc-nhin_chinh-tri-chinh-sach_news-container.html"
    assert html_file.exists()

    html_content = html_file.read_text(encoding="utf-8")
    items = listing_parser.parse_listing(html_content, category_slug="goc-nhin/chinh-tri-chinh-sach")

    assert len(items) > 0
    ajax_paging = listing_parser.extract_ajax_paging(html_content)
    assert ajax_paging is not None
    assert ajax_paging["url"] == "/ajax/goc-nhin"
    assert ajax_paging["category_id"] == "1004930"


def test_parse_infographic_and_photo_topic_post(article_parser):
    """Test parsing Infographic / Photo topic post: 9 slides, high-res images, and non-empty captions."""
    html_file = TEMPLATES_DIR / "container-detail-news_infographic-topic-post.html"
    assert html_file.exists()

    html_content = html_file.read_text(encoding="utf-8")
    url = "https://vnexpress.net/nhung-vu-cong-kich-trong-tai-noi-tieng-cua-mourinho-5123753.html"
    article = article_parser.parse(html_content, url)

    assert article is not None
    assert article.id == 5123753
    assert "Những vụ công kích trọng tài nổi tiếng của Mourinho" in article.title
    assert article.post_type in ("photo", "infographic")
    assert article.category_slug == "bong-da/la-liga"

    # Verify media extraction: exactly 9 images with captions
    assert len(article.media) == 9
    for idx, m in enumerate(article.media):
        assert m.type == "image"
        assert m.url.startswith("https://")
        assert m.caption is not None and len(m.caption) > 10, f"Media {idx} has missing or too short caption: {m.caption}"

    # Specific slide checks
    assert "Trận Chelsea - Barca, Champions League 2005" in article.media[0].caption
    assert "Por qué?" in article.media[1].caption
    assert "Chiến dịch chống Chelsea" in article.media[2].caption or "chiến dịch" in article.media[2].caption

    # Verify content text is not excessively repeated (no duplicate hidden captions)
    assert len(article.content_text) < 7000
    assert "Những vụ công kích trọng tài nổi tiếng của Mourinho" in article.content_text


def test_parse_comments_and_related_articles(article_parser):
    """Test parsing comments and related articles from container-detail-news-comment-similar.html."""
    html_file = TEMPLATES_DIR / "container-detail-news-comment-similar.html"
    assert html_file.exists()

    html_content = html_file.read_text(encoding="utf-8")
    # Wrap in minimal article container
    wrapped_html = f"<html><body><article class='fck_detail'><h1 class='title-detail'>Test</h1><p class='Normal'>Nội dung</p></article>{html_content}</body></html>"
    url = "https://vnexpress.net/test-article-5123753.html"
    article = article_parser.parse(wrapped_html, url)

    assert article is not None

    # 1. Verify Comments extraction
    assert len(article.comments) == 6
    assert article.comment_count >= 6

    # Comment 1: Alpha Trading
    c1 = next((c for c in article.comments if c.id == 64551623), None)
    assert c1 is not None
    assert c1.user_name == "Alpha Trading"
    assert c1.likes == 37
    assert c1.reply_count == 2
    assert "Nhưng chính Mou đã nói" in c1.content
    assert "Alpha Trading" not in c1.content  # Nickname should not be duplicated inside text
    assert c1.user_avatar is not None and "s61463206414946149066" in c1.user_avatar

    # Comment 2: dangchitrung
    c2 = next((c for c in article.comments if c.id == 64551251), None)
    assert c2 is not None
    assert c2.user_name == "dangchitrung"
    assert c2.likes == 30
    assert "Ngài thật tuyệt vời" in c2.content

    # Comment 3: Gấu
    c3 = next((c for c in article.comments if c.id == 64551307), None)
    assert c3 is not None
    assert c3.user_name == "Gấu"
    assert c3.likes == 22
    assert c3.reply_count == 1

    # 2. Verify Related Articles extraction
    assert len(article.related_articles) >= 20
    assert len(article.related_article_ids) >= 20

    # Specific related articles
    assert 5123203 in article.related_article_ids  # Lý do Arab Saudi hứng chịu thiệt hại...
    assert 5123520 in article.related_article_ids  # Messi được ủng hộ giành Quả Bóng Vàng...
    assert 5123554 in article.related_article_ids  # Gần 20 đội tuyển thay HLV...

    rel_5123520 = next((r for r in article.related_articles if r["id"] == 5123520), None)
    assert rel_5123520 is not None
    assert "Messi được ủng hộ giành Quả Bóng Vàng" in rel_5123520["title"]
    assert "https://vnexpress.net/messi-duoc-ung-ho-gianh-qua-bong-vang-5123520.html" == rel_5123520["url"]
