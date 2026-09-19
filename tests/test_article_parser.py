"""Unit tests for ArticleParser."""

import pytest
from datetime import datetime

from crawler.parsers.article import ArticleParser


SAMPLE_ARTICLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta property="og:image" content="https://i1-vnexpress.vnecdn.net/thumb.jpg" />
  <meta name="pubdate" content="2026-09-17T07:31:00+07:00" />
</head>
<body>
  <ul class="breadcrumb">
    <li><a href="/khoa-hoc-cong-nghe">Khoa học công nghệ</a></li>
    <li><a href="/khoa-hoc-cong-nghe/chuyen-doi-so">Chuyển đổi số</a></li>
  </ul>

  <h1 class="title-detail">Video ngắn từ YouTuber Việt tăng hơn 100% sau một năm</h1>
  <p class="description">YouTube cho biết số video Shorts từ người làm nội dung tại Việt Nam tăng 100%.</p>
  <span class="date">Thứ năm, 17/9/2026, 07:31 (GMT+7)</span>

  <article class="fck_detail">
    <div class="banner-ads"><p>Quảng cáo không mong muốn</p></div>
    <div id="_large_1">Banner lớn</div>

    <p class="Normal">Đại diện YouTube cho biết lượng người sáng tạo nội dung tại Việt Nam đang tăng trưởng mạnh.</p>

    <figure>
      <img data-src="https://i1-vnexpress.vnecdn.net/image1.jpg" src="https://i1-vnexpress.vnecdn.net/placeholder.jpg" width="1020" height="600" alt="Marc Woo" />
      <figcaption>Tổng giám đốc Google Việt Nam Marc Woo tại sự kiện. Ảnh: Lưu Quý</figcaption>
    </figure>

    <p class="Normal">Các công nghệ AI mới đã hỗ trợ đáng kể quá trình làm video.</p>

    <div class="box-tinlienquan"><a href="#">Tin liên quan khác</a></div>

    <p class="Normal"><strong>Lưu Quý</strong></p>
  </article>
</body>
</html>
"""


@pytest.fixture
def parser():
    return ArticleParser(base_url="https://vnexpress.net")


def test_parse_article_details(parser):
    url = "https://vnexpress.net/video-ngan-tu-youtuber-viet-tang-hon-100-sau-mot-nam-5121093.html"
    article = parser.parse(SAMPLE_ARTICLE_HTML, url)

    assert article is not None
    assert article.id == 5121093
    assert article.title == "Video ngắn từ YouTuber Việt tăng hơn 100% sau một năm"
    assert "video Shorts" in article.description
    assert article.author == "Lưu Quý"
    assert article.category_slug == "khoa-hoc-cong-nghe/chuyen-doi-so"
    assert article.thumbnail_url == "https://i1-vnexpress.vnecdn.net/thumb.jpg"
    assert article.published_at is not None

    # Check media extraction
    assert len(article.media) == 1
    media = article.media[0]
    assert media.type == "image"
    assert media.url == "https://i1-vnexpress.vnecdn.net/image1.jpg"
    assert "Marc Woo tại sự kiện" in media.caption

    # Check that junk elements were stripped from content_html
    assert "banner-ads" not in article.content_html
    assert "Quảng cáo không mong muốn" not in article.content_html
    assert "_large_1" not in article.content_html
    assert "box-tinlienquan" not in article.content_html

    # Check content_text
    assert "Đại diện YouTube" in article.content_text
    assert "Lưu Quý" in article.content_text
    assert "<" not in article.content_text  # pure text, no html tags
