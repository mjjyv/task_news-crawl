"""Integration tests for Category API endpoints."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.dependencies import get_db
from backend.main import app
from crawler.storage.models import Article, Base, Category


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

    # Seed test categories
    parent = Category(
        name="Khoa học",
        slug="khoa-hoc",
        origin_url="https://vnexpress.net/khoa-hoc",
    )
    sess.add(parent)
    sess.flush()

    child = Category(
        name="Trí tuệ nhân tạo",
        slug="khoa-hoc/ai",
        origin_url="https://vnexpress.net/khoa-hoc/ai",
        parent_id=parent.id,
    )
    sess.add(child)
    sess.flush()

    # Seed sample articles
    art1 = Article(
        id=1001,
        title="Đột phá AI năm 2026",
        slug="dot-pha-ai-nam-2026-1001",
        description="Mô tả AI",
        content_html="<p>Nội dung</p>",
        content_text="Nội dung AI",
        origin_url="https://vnexpress.net/1001.html",
        category_id=child.id,
        published_at=datetime.now(timezone.utc),
    )
    sess.add(art1)
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


def test_list_categories_tree(client):
    response = client.get("/api/v1/categories?tree=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    root = data[0]
    assert root["slug"] == "khoa-hoc"
    assert root["article_count"] == 1  # Rolled up from child
    assert len(root["children"]) == 1
    assert root["children"][0]["slug"] == "khoa-hoc/ai"
    assert root["children"][0]["article_count"] == 1


def test_list_categories_flat(client):
    response = client.get("/api/v1/categories?tree=false")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_category_by_slug_parent(client):
    response = client.get("/api/v1/categories/khoa-hoc")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Khoa học"
    assert data["article_count"] == 1
    assert len(data["children"]) == 1
    assert data["children"][0]["slug"] == "khoa-hoc/ai"


def test_get_category_by_slug_nested(client):
    response = client.get("/api/v1/categories/khoa-hoc/ai")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Trí tuệ nhân tạo"
    assert data["parent"] is not None
    assert data["parent"]["slug"] == "khoa-hoc"
    assert data["article_count"] == 1


def test_get_category_not_found(client):
    response = client.get("/api/v1/categories/non-existent-category")
    assert response.status_code == 404
    assert "detail" in response.json()
