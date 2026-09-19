"""Unit tests for Storage layer (Models, Database, Repository)."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crawler.storage.models import Base
from crawler.storage.repository import Repository


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    sess = SessionFactory()
    yield sess
    sess.close()


def test_category_crud(session):
    repo = Repository(session)

    # 1. Create parent category
    parent = repo.upsert_category(
        name="Khoa học công nghệ",
        slug="khoa-hoc-cong-nghe",
        origin_url="https://vnexpress.net/khoa-hoc-cong-nghe",
    )
    assert parent.id is not None
    assert parent.slug == "khoa-hoc-cong-nghe"

    # 2. Create subcategory
    child = repo.upsert_category(
        name="AI",
        slug="khoa-hoc-cong-nghe/ai",
        origin_url="https://vnexpress.net/khoa-hoc-cong-nghe/ai",
        parent_id=parent.id,
    )
    assert child.parent_id == parent.id

    # 3. Retrieve
    retrieved = repo.get_category_by_slug("khoa-hoc-cong-nghe/ai")
    assert retrieved is not None
    assert retrieved.parent.name == "Khoa học công nghệ"

    all_cats = repo.get_all_categories()
    assert len(all_cats) == 2


def test_article_and_media_crud(session):
    repo = Repository(session)

    cat = repo.upsert_category(
        name="Thời sự",
        slug="thoi-su",
        origin_url="https://vnexpress.net/thoi-su",
    )

    art_data = {
        "id": 5122237,
        "title": "Gemini tấn công mạng",
        "slug": "gemini-tan-cong-mang-5122237",
        "description": "Sapo description",
        "content_html": "<p>Nội dung</p>",
        "content_text": "Nội dung text",
        "author": "Chuyên gia",
        "thumbnail_url": "https://img.vnecdn.net/thumb.jpg",
        "origin_url": "https://vnexpress.net/gemini-5122237.html",
        "category_id": cat.id,
        "published_at": datetime.now(timezone.utc),
    }

    media_items = [
        {
            "type": "image",
            "url": "https://img.vnecdn.net/pic1.jpg",
            "caption": "Mô tả ảnh 1",
            "width": 680,
            "height": 408,
        }
    ]

    # Create
    art = repo.upsert_article(art_data, media_items)
    assert art.id == 5122237
    assert len(art.media) == 1
    assert art.media[0].caption == "Mô tả ảnh 1"

    # Retrieve
    saved_art = repo.get_article_by_id(5122237)
    assert saved_art is not None
    assert saved_art.title == "Gemini tấn công mạng"
    assert saved_art.category.name == "Thời sự"

    # Count
    count = repo.count_articles()
    assert count == 1


def test_crawl_logs_and_stats(session):
    repo = Repository(session)

    repo.log_crawl(
        crawler_type="listing",
        target_url="https://vnexpress.net/thoi-su",
        status="success",
        articles_found=20,
        articles_new=15,
    )

    stats = repo.get_stats()
    assert len(stats["latest_logs"]) == 1
    assert stats["latest_logs"][0]["found"] == 20
    assert stats["latest_logs"][0]["new"] == 15
