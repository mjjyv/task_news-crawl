"""Unit tests for RSSParser."""

import pytest
from crawler.parsers.rss import RSSParser

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>Tin mới nhất - VnExpress RSS</title>
    <link>https://vnexpress.net</link>
    <description>VnExpress RSS</description>
    <item>
      <title><![CDATA[Gemini tấn công mạng, đoán mật khẩu người dùng]]></title>
      <description><![CDATA[<a href="https://vnexpress.net/gemini-tan-cong-mang-doan-mat-khau-nguoi-dung-5122237.html"><img src="https://i1-vnexpress.vnecdn.net/thumb_gemini.jpg" ></a>Google thừa nhận mô hình Gemini đã tấn công một số hệ thống.]]></description>
      <pubDate>Sat, 19 Sep 2026 18:00:00 +0700</pubDate>
      <link>https://vnexpress.net/gemini-tan-cong-mang-doan-mat-khau-nguoi-dung-5122237.html</link>
      <guid>https://vnexpress.net/gemini-tan-cong-mang-doan-mat-khau-nguoi-dung-5122237.html</guid>
    </item>
    <item>
      <title><![CDATA[Bốn smartphone gập có tỷ lệ màn hình gần 4:3]]></title>
      <description><![CDATA[<a href="https://vnexpress.net/bon-smartphone-gap-co-ty-le-man-hinh-gan-4-3-5120242.html"><img src="https://i1-vnexpress.vnecdn.net/thumb_fold.jpg" ></a>Apple, Samsung, Xiaomi và Huawei đều có phiên bản smartphone màn hình gập.]]></description>
      <pubDate>Tue, 15 Sep 2026 10:00:00 +0700</pubDate>
      <link>https://vnexpress.net/bon-smartphone-gap-co-ty-le-man-hinh-gan-4-3-5120242.html</link>
      <guid>https://vnexpress.net/bon-smartphone-gap-co-ty-le-man-hinh-gan-4-3-5120242.html</guid>
    </item>
  </channel>
</rss>
"""


@pytest.fixture
def parser():
    return RSSParser()


def test_parse_rss(parser):
    items = parser.parse(SAMPLE_RSS_XML)
    assert len(items) == 2

    gemini = items[0]
    assert gemini.title == "Gemini tấn công mạng, đoán mật khẩu người dùng"
    assert gemini.article_id == 5122237
    assert gemini.thumbnail_url == "https://i1-vnexpress.vnecdn.net/thumb_gemini.jpg"
    assert "Google thừa nhận mô hình Gemini" in gemini.description
    assert "<img" not in gemini.description  # Cleaned HTML inside description
    assert gemini.pub_date is not None

    fold = items[1]
    assert fold.article_id == 5120242
    assert fold.thumbnail_url == "https://i1-vnexpress.vnecdn.net/thumb_fold.jpg"
