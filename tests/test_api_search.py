"""Integration tests for Search API endpoints."""

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

    cat1 = Category(name="Khoa học", slug="khoa-hoc", origin_url="https://vnexpress.net/khoa-hoc")
    cat2 = Category(name="Thời sự", slug="thoi-su", origin_url="https://vnexpress.net/thoi-su")
    sess.add_all([cat1, cat2])
    sess.flush()

    art1 = Article(
        id=3001,
        title="Trí tuệ nhân tạo đột phá trong y tế",
        slug="tri-tue-nhan-tao-dot-pha-trong-y-te-3001",
        description="Mô hình ngôn ngữ lớn hỗ trợ chẩn đoán bệnh án chuẩn xác hơn.",
        content_html="<p>Công nghệ trí tuệ nhân tạo đang thay đổi y học toàn cầu nhanh chóng.</p>",
        content_text="Công nghệ trí tuệ nhân tạo đang thay đổi y học toàn cầu nhanh chóng.",
        origin_url="https://vnexpress.net/3001.html",
        category_id=cat1.id,
        published_at=datetime.now(timezone.utc),
    )
    art2 = Article(
        id=3002,
        title="Đường sắt cao tốc Bắc Nam đón nhận vốn đầu tư",
        slug="duong-sat-cao-toc-bac-nam-3002",
        description="Dự án giao thông hạ tầng quy mô quốc gia.",
        content_html="<p>Bộ Xây dựng và Giao thông thảo luận kế hoạch triển khai tuyến đường sắt.</p>",
        content_text="Bộ Xây dựng và Giao thông thảo luận kế hoạch triển khai tuyến đường sắt.",
        origin_url="https://vnexpress.net/3002.html",
        category_id=cat2.id,
        published_at=datetime.now(timezone.utc),
    )
    sess.add_all([art1, art2])
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


def test_search_accented_vietnamese(client):
    # Search accented "trí tuệ nhân tạo"
    response = client.get("/api/v1/search", params={"q": "trí tuệ nhân tạo"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == 3001
    assert data["items"][0]["score"] > 0
    assert "trí tuệ nhân tạo" in data["items"][0]["snippet"].lower()


def test_search_unaccented_vietnamese(client):
    # Search unaccented "tri tue nhan tao" should match "Trí tuệ nhân tạo"
    response = client.get("/api/v1/search", params={"q": "tri tue nhan tao"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == 3001


def test_search_with_d_stroke(client):
    # Search "dot pha" should match "đột phá"
    response = client.get("/api/v1/search", params={"q": "dot pha"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == 3001


def test_search_content_text(client):
    # Search keyword only in content: "kế hoạch triển khai"
    response = client.get("/api/v1/search", params={"q": "ke hoach trien khai"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == 3002


def test_search_with_category_filter(client):
    # Search keyword in wrong category should return 0
    response = client.get("/api/v1/search", params={"q": "trí tuệ nhân tạo", "category": "thoi-su"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0

    # Search in correct category returns match
    response = client.get("/api/v1/search", params={"q": "trí tuệ nhân tạo", "category": "khoa-hoc"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_search_validation_empty_query(client):
    response = client.get("/api/v1/search?q=")
    assert response.status_code == 422  # min_length=1 validation error
