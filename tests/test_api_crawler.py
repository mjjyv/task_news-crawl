"""Integration tests for Crawler & System API endpoints."""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.dependencies import get_db
from backend.main import app
from crawler.storage.models import Base


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


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "endpoints" in data
    assert "documentation" in data
    assert "X-Process-Time" in response.headers


def test_liveness_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_crawler_health_dashboard(client):
    response = client.get("/api/v1/crawler/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database_connected"] is True
    assert "status" in data
    assert "total_categories" in data
    assert "total_articles" in data
    assert "total_media" in data
    assert "seen_ids_count" in data
    assert "latest_logs" in data


def test_crawler_trigger_rss_task(client):
    with patch("backend.services.crawler_service.CrawlerService.execute_crawl_task") as mock_crawl:
        payload = {
            "type": "rss",
            "target": "tin-moi-nhat",
            "max_articles": 5,
        }
        response = client.post("/api/v1/crawler/trigger", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["task_type"] == "rss"
        assert data["target"] == "tin-moi-nhat"
        mock_crawl.assert_called_once_with(
            task_type="rss",
            target="tin-moi-nhat",
            pages=1,
            max_articles=5,
        )


def test_crawler_trigger_category_task(client):
    with patch("backend.services.crawler_service.CrawlerService.execute_crawl_task") as mock_crawl:
        payload = {
            "type": "category",
            "target": "khoa-hoc",
            "pages": 2,
            "max_articles": 15,
        }
        response = client.post("/api/v1/crawler/trigger", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["task_type"] == "category"
        assert data["target"] == "khoa-hoc"
        mock_crawl.assert_called_once_with(
            task_type="category",
            target="khoa-hoc",
            pages=2,
            max_articles=15,
        )
