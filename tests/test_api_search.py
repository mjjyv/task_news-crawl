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
    art3 = Article(
        id=3003,
        title="Người dân chi tiền mua điện thoại mới",
        slug="nguoi-dan-chi-tien-mua-dien-thoai-moi-3003",
        description="Doanh số các cửa hàng bán lẻ tăng mạnh trong ngày đầu mở bán.",
        content_html="<p>Rất đông khách hàng đến xếp hàng để mua sắm thiết bị công nghệ.</p>",
        content_text="Rất đông khách hàng đến xếp hàng để mua sắm thiết bị công nghệ.",
        origin_url="https://vnexpress.net/3003.html",
        category_id=cat1.id,
        published_at=datetime.now(timezone.utc),
    )
    art4 = Article(
        id=3004,
        title="Mưa lớn kéo dài gây ngập lụt tại Hà Nội",
        slug="mua-lon-keo-dai-gay-ngap-lut-tai-ha-noi-3004",
        description="Trận mưa lớn khiến nhiều tuyến đường trung tâm thủ đô ngập sâu trong nước.",
        content_html="<p>Hàng loạt phương tiện chết máy khi di chuyển qua các điểm ngập nước.</p>",
        content_text="Hàng loạt phương tiện chết máy khi di chuyển qua các điểm ngập nước.",
        origin_url="https://vnexpress.net/3004.html",
        category_id=cat2.id,
        published_at=datetime.now(timezone.utc),
    )
    art5 = Article(
        id=3005,
        title="Thiết bị theo dõi giấc ngủ thông minh",
        slug="thiet-bi-theo-doi-giac-ngu-thong-minh-3005",
        description="Công nghệ theo dõi nhịp thở và chất lượng giấc ngủ ban đêm.",
        content_html="<p>Thiết bị đeo tay giúp đo chu kỳ ngủ sâu và thức giấc.</p>",
        content_text="Thiết bị đeo tay giúp đo chu kỳ ngủ sâu và thức giấc.",
        origin_url="https://vnexpress.net/3005.html",
        category_id=cat1.id,
        published_at=datetime.now(timezone.utc),
    )
    art6 = Article(
        id=3006,
        title="Đội ngũ kỹ sư phần mềm xuất sắc",
        slug="doi-ngu-ky-su-phan-mem-xuat-sac-3006",
        description="Xây dựng đội ngũ nhân sự chất lượng cao cho doanh nghiệp.",
        content_html="<p>Phát triển năng lực cho đội ngũ kỹ sư công nghệ.</p>",
        content_text="Phát triển năng lực cho đội ngũ kỹ sư công nghệ.",
        origin_url="https://vnexpress.net/3006.html",
        category_id=cat1.id,
        published_at=datetime.now(timezone.utc),
    )
    sess.add_all([art1, art2, art3, art4, art5, art6])
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


def test_search_accent_preservation_avoids_false_positive(client):
    # Accented query "mưa ngập" must match article 3004 (rain & flood)
    # and MUST NOT match article 3003 (purchasing phone "mua điện thoại")
    response = client.get("/api/v1/search", params={"q": "mưa ngập"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == 3004


def test_search_ha_noi_precision(client):
    # Query "ha noi" must match article 3004 (which has "Hà Nội"), and not match other articles
    response = client.get("/api/v1/search", params={"q": "ha noi"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == 3004
    assert "hà nội" in data["items"][0]["snippet"].lower()


def test_search_exact_accent_mode(client):
    # In exact accent mode (exact_accent=true), searching "ngủ" must match ONLY article 3005 ("giấc ngủ")
    # and MUST NOT match article 3006 ("đội ngũ") or other articles
    response = client.get("/api/v1/search", params={"q": "ngủ", "exact_accent": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["exact_accent"] is True
    assert data["total"] == 1
    assert data["items"][0]["id"] == 3005
    assert "ngủ" in data["items"][0]["snippet"].lower()


def test_search_unaccented_mode_word_boundary(client):
    # In unaccented mode (exact_accent=false), searching "ngu" matches:
    # 3001 ("ngôn ngữ" -> "ngu"), 3005 ("giấc ngủ" -> "ngu"), 3006 ("đội ngũ" -> "ngu")
    # and MUST NOT match 3002, 3003, 3004 containing "người"
    response = client.get("/api/v1/search", params={"q": "ngu", "exact_accent": "false"})
    assert response.status_code == 200
    data = response.json()
    assert data["exact_accent"] is False
    assert data["total"] == 3
    matched_ids = {item["id"] for item in data["items"]}
    assert matched_ids == {3001, 3005, 3006}
