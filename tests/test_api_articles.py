"""Integration tests for Article API endpoints."""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.dependencies import get_db
from backend.main import app
from crawler.storage.models import Article, Base, Category, Media


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

    # Seed categories
    parent_cat = Category(
        name="Thời sự",
        slug="thoi-su",
        origin_url="https://vnexpress.net/thoi-su",
    )
    sess.add(parent_cat)
    sess.flush()

    child_cat = Category(
        name="Giao thông",
        slug="thoi-su/giao-thong",
        origin_url="https://vnexpress.net/thoi-su/giao-thong",
        parent_id=parent_cat.id,
    )
    other_cat = Category(
        name="Kinh doanh",
        slug="kinh-doanh",
        origin_url="https://vnexpress.net/kinh-doanh",
    )
    sess.add_all([child_cat, other_cat])
    sess.flush()

    # Seed articles
    now = datetime.now(timezone.utc)
    art1 = Article(
        id=2001,
        title="Dự án vành đai 4 khởi công",
        slug="du-an-vanh-dai-4-khoi-cong-2001",
        description="Khởi công dự án trọng điểm",
        content_html="<p>Chi tiết vành đai 4...</p>",
        content_text="Chi tiết vành đai 4...",
        origin_url="https://vnexpress.net/2001.html",
        category_id=child_cat.id,
        published_at=now - timedelta(days=2),
        comment_count=5,
    )
    art2 = Article(
        id=2002,
        title="Ùn tắc cao tốc dịp lễ",
        slug="un-tac-cao-toc-dip-le-2002",
        description="Giao thông căng thẳng",
        content_html="<p>Tình hình kẹt xe...</p>",
        content_text="Tình hình kẹt xe...",
        origin_url="https://vnexpress.net/2002.html",
        category_id=child_cat.id,
        published_at=now - timedelta(days=1),
        comment_count=80,
    )
    art3 = Article(
        id=2003,
        title="Thị trường chứng khoán tăng điểm",
        slug="thi-truong-chung-khoan-tang-diem-2003",
        description="VN-Index vượt đỉnh",
        content_html="<p>Kinh doanh sôi động...</p>",
        content_text="Kinh doanh sôi động...",
        origin_url="https://vnexpress.net/2003.html",
        category_id=other_cat.id,
        published_at=now,
        comment_count=20,
    )
    sess.add_all([art1, art2, art3])
    sess.flush()

    # Add media to art1
    m1 = Media(
        article_id=art1.id,
        type="image",
        url="https://img.vnecdn.net/vanhdai4.jpg",
        caption="Lễ khởi công",
        width=800,
        height=500,
    )
    sess.add(m1)
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


def test_list_articles_pagination(client):
    response = client.get("/api/v1/articles?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 2
    assert len(data["items"]) == 2


def test_list_articles_category_filter_recursive(client):
    # Filter by parent category 'thoi-su' should include articles in 'thoi-su/giao-thong'
    response = client.get("/api/v1/articles?category=thoi-su")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["category"]["slug"] == "thoi-su/giao-thong"


def test_list_articles_date_filtering(client):
    now = datetime.now(timezone.utc)
    from_time = (now - timedelta(hours=12)).isoformat()
    response = client.get("/api/v1/articles", params={"from_date": from_time})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == 2003


def test_list_articles_order(client):
    # Ascending order (oldest first)
    response = client.get("/api/v1/articles?order=asc")
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["id"] == 2001
    assert data["items"][-1]["id"] == 2003


def test_get_article_detail_success(client):
    response = client.get("/api/v1/articles/2001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2001
    assert data["title"] == "Dự án vành đai 4 khởi công"
    assert data["content_html"] == "<p>Chi tiết vành đai 4...</p>"
    assert len(data["media"]) == 1
    assert data["media"][0]["caption"] == "Lễ khởi công"
    # Related articles in same category (should include 2002)
    assert len(data["related_articles"]) == 1
    assert data["related_articles"][0]["id"] == 2002


def test_get_article_detail_not_found(client):
    response = client.get("/api/v1/articles/999999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_list_articles_sort_hot(client):
    # Hot sorting should return articles sorted by comment_count desc (80 -> 20 -> 5)
    response = client.get("/api/v1/articles?sort=hot")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["items"][0]["id"] == 2002
    assert data["items"][0]["comment_count"] == 80
    assert data["items"][1]["id"] == 2003
    assert data["items"][1]["comment_count"] == 20
    assert data["items"][2]["id"] == 2001
    assert data["items"][2]["comment_count"] == 5


def test_list_articles_min_comments_filter(client):
    # Filter min_comments=10 should return only articles with comment_count >= 10
    response = client.get("/api/v1/articles?min_comments=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["comment_count"] >= 10
    ids = [item["id"] for item in data["items"]]
    assert 2002 in ids
    assert 2003 in ids
    assert 2001 not in ids
