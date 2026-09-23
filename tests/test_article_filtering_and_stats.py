"""Integration tests for Article filtering by post_type and Crawler health stats with comments."""

from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.dependencies import get_db
from backend.main import app
from crawler.storage.models import Article, Base, Category, Comment, Media


@pytest.fixture
def session():
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

    # Seed articles with different post_types
    now = datetime.now(timezone.utc)
    art_text = Article(
        id=3001,
        title="Bài báo dạng văn bản",
        slug="bai-bao-van-ban-3001",
        description="Mô tả văn bản",
        content_html="<p>Văn bản...</p>",
        content_text="Văn bản...",
        origin_url="https://vnexpress.net/3001.html",
        category_id=cat.id,
        post_type="text",
        published_at=now,
    )
    art_photo = Article(
        id=3002,
        title="Bài báo dạng chùm ảnh",
        slug="bai-bao-chum-anh-3002",
        description="Mô tả chùm ảnh",
        content_html="<p>Chùm ảnh...</p>",
        content_text="Chùm ảnh...",
        origin_url="https://vnexpress.net/3002.html",
        category_id=cat.id,
        post_type="photo",
        published_at=now,
    )
    art_info = Article(
        id=3003,
        title="Bài báo dạng infographic",
        slug="bai-bao-infographic-3003",
        description="Mô tả infographic",
        content_html="<p>Infographic...</p>",
        content_text="Infographic...",
        origin_url="https://vnexpress.net/3003.html",
        category_id=cat.id,
        post_type="infographic",
        published_at=now,
    )
    sess.add_all([art_text, art_photo, art_info])
    sess.flush()

    # Seed a comment
    cmt = Comment(
        id=4001,
        article_id=art_photo.id,
        user_name="Doc Gia",
        content="Ảnh rất đẹp",
        likes=10,
    )
    sess.add(cmt)
    sess.commit()

    yield sess
    sess.close()


@pytest.fixture
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_filter_articles_by_post_type(client):
    # 1. Filter post_type=photo
    resp_photo = client.get("/api/v1/articles?post_type=photo")
    assert resp_photo.status_code == 200
    data_photo = resp_photo.json()
    assert data_photo["total"] == 1
    assert data_photo["items"][0]["id"] == 3002
    assert data_photo["items"][0]["post_type"] == "photo"

    # 2. Filter post_type=infographic
    resp_info = client.get("/api/v1/articles?post_type=infographic")
    assert resp_info.status_code == 200
    data_info = resp_info.json()
    assert data_info["total"] == 1
    assert data_info["items"][0]["id"] == 3003
    assert data_info["items"][0]["post_type"] == "infographic"

    # 3. Filter post_type=text
    resp_text = client.get("/api/v1/articles?post_type=text")
    assert resp_text.status_code == 200
    data_text = resp_text.json()
    assert data_text["total"] == 1
    assert data_text["items"][0]["id"] == 3001

    # 4. No filter returns all 3
    resp_all = client.get("/api/v1/articles")
    assert resp_all.status_code == 200
    assert resp_all.json()["total"] == 3


def test_crawler_health_includes_total_comments(client):
    resp = client.get("/api/v1/crawler/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["total_articles"] == 3
    assert data["total_comments"] == 1


def test_trigger_backfill_endpoint(client):
    with patch("backend.services.crawler_service.CrawlerService.execute_backfill_task") as mock_backfill:
        payload = {
            "mode": "missing-media",
            "limit": 10,
            "delay": 0.0,
        }
        resp = client.post("/api/v1/crawler/backfill", json=payload)
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["mode"] == "missing-media"
        assert data["limit"] == 10
        mock_backfill.assert_called_once_with(
            mode="missing-media",
            limit=10,
            category=None,
            delay=0.0,
        )
