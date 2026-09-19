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


def test_parse_gallery_and_video_article(parser):
    """Test extracting gallery items, video, and audio from diverse article structures."""
    gallery_html = """
    <html>
    <head><meta name="tt_article_id" content="5121340" /></head>
    <body>
      <h1 class="title-detail">Người Hà Nội tát nước, bơi xuồng ngày mưa ngập</h1>
      <p class="description">Mưa lớn sau bão khiến nhiều tuyến phố thủ đô ngập sâu.</p>
      <span class="date">17/9/2026, 12:00</span>
      <article class="fck_detail">
        <figure>
          <div class="gallery_block">
            <div class="item_gallery_new">
              <img data-desktop-src="https://img.vnecdn.net/gal1.jpg" data-caption="&lt;p&gt;Người dân chèo xuồng trên phố. Ảnh: &lt;em&gt;VNE&lt;/em&gt;&lt;/p&gt;" />
            </div>
            <div class="item_gallery_new">
              <img data-desktop-src="https://img.vnecdn.net/gal2.jpg" data-caption="&lt;p&gt;Xe máy chết máy la liệt.&lt;/p&gt;" />
            </div>
          </div>
        </figure>
        <div data-video="https://video.vnecdn.net/clip1.mp4" title="Video ngập phố"></div>
        <audio data-audio="https://audio.vnecdn.net/podcast1.mp3" title="Bản tin audio"></audio>
        <p class="Normal"><strong>Gia Chính</strong></p>
      </article>
    </body>
    </html>
    """
    url = "https://vnexpress.net/nguoi-ha-noi-tat-nuoc-boi-xuong-ngay-mua-ngap-5121340.html"
    parsed = parser.parse(gallery_html, url)

    assert parsed is not None
    assert parsed.id == 5121340
    assert parsed.author == "Gia Chính"

    # Verify images, video, and audio were extracted
    media_types = [m.type for m in parsed.media]
    assert "image" in media_types
    assert "video" in media_types
    assert "audio" in media_types

    # Verify caption unescaping
    img1 = next(m for m in parsed.media if m.url == "https://img.vnecdn.net/gal1.jpg")
    assert "Người dân chèo xuồng trên phố" in img1.caption
    assert "<p>" not in img1.caption  # Cleaned HTML tags from caption

    video = next(m for m in parsed.media if m.type == "video")
    assert video.url == "https://video.vnecdn.net/clip1.mp4"
    assert video.caption == "Video ngập phố"

