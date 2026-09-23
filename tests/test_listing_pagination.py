"""Unit tests for listing pagination logic (standard -p{page}, AJAX endpoints, and dynamic switching)."""

from unittest.mock import MagicMock, patch
import pytest

from crawler.parsers.listing import ListingParser
from crawler.pipeline.article_pipeline import ArticlePipeline
from crawler.storage.database import get_db_session
from crawler.storage.models import Base
from crawler.storage.repository import Repository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def listing_parser():
    return ListingParser(base_url="https://vnexpress.net")


def test_extract_ajax_paging_various_formats(listing_parser):
    # Format 1: div#paging with data-url and data-category
    html1 = """
    <div id="paging" data-url="/ajax/goc-nhin" data-container="paging"
         data-category="1003450" data-page="2" data-exclude="3">
    </div>
    """
    res1 = listing_parser.extract_ajax_paging(html1)
    assert res1 is not None
    assert res1["url"] == "/ajax/goc-nhin"
    assert res1["category_id"] == "1003450"
    assert res1["page"] == 2
    assert res1["exclude"] == "3"

    # Format 2: container with data-cate-id
    html2 = """
    <div class="list-stream" data-container="paging" data-url="/ajax/category"
         data-cate-id="1001234" data-page="3">
    </div>
    """
    res2 = listing_parser.extract_ajax_paging(html2)
    assert res2 is not None
    assert res2["url"] == "/ajax/category"
    assert res2["category_id"] == "1001234"
    assert res2["page"] == 3

    # Format 3: No AJAX paging
    html3 = "<div class='standard-list'><p>No ajax here</p></div>"
    assert listing_parser.extract_ajax_paging(html3) is None


def test_build_ajax_page_url(listing_parser):
    ajax_info = {
        "url": "/ajax/goc-nhin",
        "category_id": "1003450",
        "page": 2,
        "exclude": "3",
    }
    url_p2 = listing_parser.build_ajax_page_url(ajax_info, page_num=2)
    assert url_p2 == "https://vnexpress.net/ajax/goc-nhin?category_id=1003450&page=2&exclude=3"

    url_p5 = listing_parser.build_ajax_page_url(ajax_info, page_num=5)
    assert url_p5 == "https://vnexpress.net/ajax/goc-nhin?category_id=1003450&page=5&exclude=3"


def test_extract_pagination_links(listing_parser):
    html = """
    <div class="pagination">
        <a href="/thoi-su">1</a>
        <a href="/thoi-su-p2">2</a>
        <a href="/thoi-su-p3" class="btn-page">3</a>
        <a href="javascript:void(0)">Next</a>
    </div>
    """
    links = listing_parser.extract_pagination(html)
    assert len(links) == 3
    assert "https://vnexpress.net/thoi-su" in links
    assert "https://vnexpress.net/thoi-su-p2" in links
    assert "https://vnexpress.net/thoi-su-p3" in links


def test_crawl_category_dynamic_ajax_switching():
    """Verify ArticlePipeline automatically detects AJAX pagination on page 1 and uses it for page 2."""
    html_page1 = """
    <html>
        <body>
            <div id="paging" data-url="/ajax/goc-nhin" data-category="1003450" data-page="2" data-exclude="3">
                <article class="item-news">
                    <h3 class="title-news"><a href="https://vnexpress.net/bai-viet-1-5000001.html">Bài viết 1</a></h3>
                    <p class="description">Mô tả 1</p>
                </article>
            </div>
        </body>
    </html>
    """

    html_page2 = """
    <div>
        <article class="item-news">
            <h3 class="title-news"><a href="https://vnexpress.net/bai-viet-2-5000002.html">Bài viết 2</a></h3>
            <p class="description">Mô tả 2</p>
        </article>
    </div>
    """

    mock_client = MagicMock()

    def mock_fetch(url):
        mock_resp = MagicMock()
        if "ajax/goc-nhin" in url:
            mock_resp.text = html_page2
        else:
            mock_resp.text = html_page1
        return mock_resp

    mock_client.fetch.side_effect = mock_fetch

    mock_dedup = MagicMock()
    mock_dedup.filter_unseen.side_effect = lambda ids: ids

    pipeline = ArticlePipeline(http_client=mock_client, deduplicator=mock_dedup)

    with patch.object(pipeline, "_fetch_and_save_article", return_value=True):
        res = pipeline.crawl_category(category_slug="goc-nhin", max_pages=2, recursive=False)

    assert res["articles_found"] == 2
    assert res["articles_new"] == 2

    # Verify that the second call was made to the AJAX URL
    called_urls = [call.args[0] for call in mock_client.fetch.call_args_list]
    assert len(called_urls) == 2
    assert "https://vnexpress.net/goc-nhin" == called_urls[0]
    assert "https://vnexpress.net/ajax/goc-nhin?category_id=1003450&page=2&exclude=3" == called_urls[1]
