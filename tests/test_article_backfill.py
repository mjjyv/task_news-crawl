"""Unit and integration tests for ArticleBackfillPipeline."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crawler.pipeline.article_backfill import ArticleBackfillPipeline
from crawler.storage.models import Article, Base, Category, Comment, Media
from crawler.storage.repository import Repository


@pytest.fixture
def mock_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

    sess = SessionFactory()
    # Seed category
    cat = Category(name="Khoa học", slug="khoa-hoc", origin_url="https://vnexpress.net/khoa-hoc")
    sess.add(cat)
    sess.flush()

    # Seed article 1: Missing media, text post
    art1 = Article(
        id=7001,
        title="Khám phá hành tinh mới ngoài hệ Mặt Trời",
        slug="kham-pha-hanh-tinh-moi-7001",
        description="Phát hiện thiên văn học quan trọng",
        content_html="<p>Nội dung bài viết 1...</p>",
        content_text="Nội dung bài viết 1...",
        origin_url="https://vnexpress.net/kham-pha-hanh-tinh-moi-7001.html",
        category_id=cat.id,
        post_type="text",
        comment_count=0,
        published_at=datetime.now(timezone.utc),
    )

    # Seed article 2: Photo story with 0 media currently stored
    art2 = Article(
        id=7002,
        title="Chùm ảnh vẻ đẹp cực quang ở Bắc Cực",
        slug="chum-anh-ve-dep-cuc-quang-7002",
        description="Những dải sáng huyền ảo trên bầu trời",
        content_html="<p>Chùm ảnh Bắc Cực...</p>",
        content_text="Chùm ảnh Bắc Cực...",
        origin_url="https://vnexpress.net/cuc-quang-7002.html",
        category_id=cat.id,
        post_type="text",  # currently misclassified as text
        comment_count=15,
        published_at=datetime.now(timezone.utc),
    )

    # Seed article 3: Has 1 media without caption
    art3 = Article(
        id=7003,
        title="Robot thám hiểm sao Hỏa gửi dữ liệu",
        slug="robot-tham-hiem-sao-hoa-7003",
        description="Dữ liệu đất đá sao Hỏa",
        content_html="<p>Nội dung robot...</p>",
        content_text="Nội dung robot...",
        origin_url="https://vnexpress.net/robot-sao-hoa-7003.html",
        category_id=cat.id,
        post_type="text",
        comment_count=2,
        published_at=datetime.now(timezone.utc),
    )
    sess.add_all([art1, art2, art3])
    sess.flush()

    # Media for art3
    m3 = Media(
        article_id=art3.id,
        type="image",
        url="https://img.vnecdn.net/mars1.jpg",
        caption=None,  # missing caption
    )
    sess.add(m3)
    sess.commit()
    sess.close()

    @contextmanager
    def _mock_get_session():
        session = SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    yield SessionFactory, _mock_get_session


def test_backfill_missing_media_and_thumbnail(mock_db):
    SessionFactory, get_session = mock_db
    mock_html = """
    <html>
        <body>
            <h1 class="title-detail">Khám phá hành tinh mới ngoài hệ Mặt Trời</h1>
            <p class="description">Phát hiện thiên văn học quan trọng</p>
            <div class="fck_detail">
                <p>Nội dung khoa học chi tiết...</p>
                <figure class="tplCaption">
                    <img src="https://img.vnecdn.net/exoplanet_full.jpg" alt="Ảnh mô phỏng hành tinh" />
                    <figcaption><p class="Image">Mô phỏng hành tinh khí khổng lồ</p></figcaption>
                </figure>
            </div>
        </body>
    </html>
    """
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = mock_html
    mock_client.fetch.return_value = mock_resp

    with patch("crawler.pipeline.article_backfill.get_db_session", side_effect=get_session):
        pipeline = ArticleBackfillPipeline(http_client=mock_client)
        success = pipeline.backfill_single_article(7001)
        assert success is True

    # Verify DB state
    with SessionFactory() as sess:
        art = sess.get(Article, 7001)
        assert art is not None
        assert len(art.media) == 1
        assert art.media[0].url == "https://img.vnecdn.net/exoplanet_full.jpg"
        assert art.media[0].caption == "Mô phỏng hành tinh khí khổng lồ"
        assert art.thumbnail_url == "https://img.vnecdn.net/exoplanet_full.jpg"


def test_backfill_rich_photo_post(mock_db):
    SessionFactory, get_session = mock_db
    mock_html = """
    <html>
        <body>
            <h1 class="title-detail">Chùm ảnh vẻ đẹp cực quang ở Bắc Cực</h1>
            <p class="description">Những dải sáng huyền ảo trên bầu trời</p>
            <div class="fck_detail">
                <div class="item_slide_show" data-src="https://img.vnecdn.net/cucquang_1200.jpg">
                    <div class="block_thumb_slide_show" data-src="https://img.vnecdn.net/cucquang_1200.jpg"></div>
                    <div class="desc_cation"><p>Dải cực quang xanh ngắt tại bán đảo Tromso.</p></div>
                </div>
                <div class="item_slide_show" data-src="https://img.vnecdn.net/cucquang_2_1200.jpg">
                    <div class="block_thumb_slide_show" data-src="https://img.vnecdn.net/cucquang_2_1200.jpg"></div>
                    <div class="desc_cation"><p>Cực quang màu tím hiếm gặp.</p></div>
                </div>
            </div>
            <div class="box-tinlienquan">
                <a href="https://vnexpress.net/bai-lien-quan-7001.html">Bài liên quan 1</a>
            </div>
            <div id="list_comment">
                <div class="comment_item" data-user-id="99" data-user-name="Nguyen Nam">
                    <div class="full_name">Nguyen Nam</div>
                    <div class="content_more">Ảnh chụp quá ngoạn mục!</div>
                    <div class="reactions-total"><a class="number">35</a></div>
                </div>
            </div>
        </body>
    </html>
    """

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = mock_html
    mock_client.fetch.return_value = mock_resp

    with patch("crawler.pipeline.article_backfill.get_db_session", side_effect=get_session):
        pipeline = ArticleBackfillPipeline(http_client=mock_client)
        success = pipeline.backfill_single_article(7002)
        assert success is True

    # Verify DB state
    with SessionFactory() as sess:
        art = sess.get(Article, 7002)
        assert art.post_type == "photo"
        assert len(art.media) == 2
        assert art.media[0].url == "https://img.vnecdn.net/cucquang_1200.jpg"
        assert art.media[0].caption == "Dải cực quang xanh ngắt tại bán đảo Tromso."
        assert json.loads(art.related_article_ids) == [7001]
        assert len(art.comments) == 1
        assert art.comments[0].user_name == "Nguyen Nam"
        assert art.comments[0].likes == 35


def test_backfill_enriches_existing_media_caption(mock_db):
    SessionFactory, get_session = mock_db
    # art3 already has mars1.jpg but caption was None
    mock_html = """
    <html>
        <body>
            <h1 class="title-detail">Robot thám hiểm sao Hỏa gửi dữ liệu</h1>
            <div class="fck_detail">
                <figure class="tplCaption">
                    <img src="https://img.vnecdn.net/mars1.jpg" />
                    <figcaption><p class="Image">Cánh tay robot đang khoan mẫu đá sao Hỏa</p></figcaption>
                </figure>
            </div>
        </body>
    </html>
    """
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = mock_html
    mock_client.fetch.return_value = mock_resp

    with patch("crawler.pipeline.article_backfill.get_db_session", side_effect=get_session):
        pipeline = ArticleBackfillPipeline(http_client=mock_client)
        success = pipeline.backfill_single_article(7003)
        assert success is True

    # Verify DB: media count didn't duplicate, but caption was enriched!
    with SessionFactory() as sess:
        art = sess.get(Article, 7003)
        assert len(art.media) == 1
        assert art.media[0].caption == "Cánh tay robot đang khoan mẫu đá sao Hỏa"


def test_backfill_error_handling(mock_db):
    SessionFactory, get_session = mock_db
    mock_client = MagicMock()
    mock_client.fetch.side_effect = RuntimeError("Connection timeout")

    with patch("crawler.pipeline.article_backfill.get_db_session", side_effect=get_session):
        pipeline = ArticleBackfillPipeline(http_client=mock_client)

        # 1. Non-existent ID returns False cleanly
        assert pipeline.backfill_single_article(999999) is False

        # 2. Network error on existing ID returns False cleanly without crashing
        res = pipeline.backfill_articles_by_ids([7001], delay=0)
        assert res["total"] == 1
        assert res["updated"] == 0
        assert res["failed"] == 1
