"""Unit tests for CategoryParser."""

import pytest
from crawler.parsers.category import CategoryParser


SAMPLE_MAIN_NAV_HTML = """
<nav id="main-nav">
  <ul class="parent">
    <li><a href="/tin-tuc-24h">Mới nhất</a></li>
    <li><a href="/thoi-su">Thời sự</a></li>
    <li><a href="/the-gioi">Thế giới</a></li>
    <li><a href="/kinh-doanh">Kinh doanh</a></li>
    <li><a href="/khoa-hoc-cong-nghe">Khoa học công nghệ</a></li>
    <li><a href="javascript:;">Tất cả</a></li>
  </ul>
</nav>
"""

SAMPLE_SUB_NAV_HTML = """
<div class="sub-nav-folder">
  <ul class="ul-nav-folder">
    <li><a href="/khoa-hoc-cong-nghe/bo-khoa-hoc-va-cong-nghe">Hoạt động Bộ KH&CN</a></li>
    <li><a href="/khoa-hoc-cong-nghe/chuyen-doi-so">Chuyển đổi số</a></li>
    <li><a href="/khoa-hoc-cong-nghe/doi-moi-sang-tao">Đổi mới sáng tạo</a></li>
    <li><a href="/khoa-hoc-cong-nghe/ai">AI</a></li>
    <li><a href="/khoa-hoc-cong-nghe/vu-tru">Vũ trụ</a></li>
    <li><a href="/khoa-hoc-cong-nghe/the-gioi-tu-nhien">Thế giới tự nhiên</a></li>
    <li><a href="/khoa-hoc-cong-nghe/thiet-bi">Thiết bị</a></li>
    <li><a href="/khoa-hoc-cong-nghe/ai4vn-2026">AI4VN</a></li>
    <li><a href="/khoa-hoc-cong-nghe/tech-awards">Tech Awards</a></li>
    <li><a href="/khoa-hoc-cong-nghe/cuoc-thi-sang-kien-khoa-hoc">Sáng kiến khoa học</a></li>
  </ul>
</div>
"""


@pytest.fixture
def parser():
    return CategoryParser(base_url="https://vnexpress.net")


def test_parse_main_categories(parser):
    cats = parser.parse_main_categories(SAMPLE_MAIN_NAV_HTML)
    slugs = [c.slug for c in cats]

    assert "tin-tuc-24h" not in slugs  # Filtered out
    assert "javascript:;" not in slugs  # Filtered out
    assert "thoi-su" in slugs
    assert "the-gioi" in slugs
    assert "kinh-doanh" in slugs
    assert "khoa-hoc-cong-nghe" in slugs

    khcn = next(c for c in cats if c.slug == "khoa-hoc-cong-nghe")
    assert khcn.name == "Khoa học công nghệ"
    assert khcn.origin_url == "https://vnexpress.net/khoa-hoc-cong-nghe"
    assert khcn.parent_slug is None


def test_parse_sub_categories(parser):
    sub_cats = parser.parse_sub_categories(SAMPLE_SUB_NAV_HTML, parent_slug="khoa-hoc-cong-nghe")
    assert len(sub_cats) == 10

    slugs = [c.slug for c in sub_cats]
    assert "khoa-hoc-cong-nghe/bo-khoa-hoc-va-cong-nghe" in slugs
    assert "khoa-hoc-cong-nghe/ai" in slugs
    assert "khoa-hoc-cong-nghe/thiet-bi" in slugs

    ai_cat = next(c for c in sub_cats if c.slug == "khoa-hoc-cong-nghe/ai")
    assert ai_cat.name == "AI"
    assert ai_cat.parent_slug == "khoa-hoc-cong-nghe"
    assert ai_cat.origin_url == "https://vnexpress.net/khoa-hoc-cong-nghe/ai"
