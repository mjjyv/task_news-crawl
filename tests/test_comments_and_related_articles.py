"""Unit and integration tests for Phase 2:
- Migration backward-compatibility
- Models & Repository (post_type, related_article_ids, Comment model)
- Comment sorting and CASCADE deletion
- API responses with comments and related articles
"""

import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.dependencies import get_db
from backend.main import app
from crawler.storage.database import init_db, migrate_db
from crawler.storage.models import Article, Base, Category, Comment, Media
from crawler.storage.repository import Repository


def test_database_migration_backward_compatible():
    """Verify migrate_db safely alters legacy schema without data loss."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # 1. Create legacy table without post_type, related_article_ids, or comments
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE articles (
                id BIGINT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                slug VARCHAR(500) NOT NULL,
                description TEXT,
                content_html TEXT,
                content_text TEXT,
                author VARCHAR(255),
                thumbnail_url VARCHAR(500),
                origin_url VARCHAR(500) NOT NULL UNIQUE,
                category_id INTEGER,
                published_at DATETIME,
                comment_count INTEGER DEFAULT 0 NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT INTO articles (id, title, slug, origin_url, comment_count)
            VALUES (1001, 'Tin tức cũ', 'tin-tuc-cu-1001', 'https://vnexpress.net/1001.html', 10);
        """
            )
        )
        conn.commit()

    # 2. Run init_db / migrate_db
    init_db(engine)

    # 3. Check schema & data preservation
    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(articles)")).fetchall()]
        assert "post_type" in cols
        assert "related_article_ids" in cols

        # Check comment table exists
        tables = [r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()]
        assert "comments" in tables

        # Check existing data is intact
        row = conn.execute(text("SELECT id, title, post_type, related_article_ids FROM articles WHERE id = 1001")).fetchone()
        assert row is not None
        assert row[0] == 1001
        assert row[1] == "Tin tức cũ"
        assert row[2] == "text"  # default post_type
        assert row[3] is None


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Enable foreign keys for SQLite so CASCADE delete works
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    sess = SessionFactory()
    yield sess
    sess.close()


def test_upsert_article_with_post_type_and_related_ids(session):
    repo = Repository(session)

    art_data = {
        "id": 5001,
        "title": "Chùm ảnh lễ hội hoa xuân",
        "slug": "chum-anh-le-hoi-hoa-xuan-5001",
        "description": "Hình ảnh tuyệt đẹp",
        "content_html": "<p>Nội dung ảnh</p>",
        "content_text": "Nội dung ảnh",
        "author": "Nhiếp ảnh gia",
        "thumbnail_url": "https://img.vnecdn.net/hoa.jpg",
        "origin_url": "https://vnexpress.net/hoa-5001.html",
        "post_type": "photo",
        "related_article_ids": [5002, 5003],
    }

    art = repo.upsert_article(art_data)
    assert art.id == 5001
    assert art.post_type == "photo"
    assert json.loads(art.related_article_ids) == [5002, 5003]

    retrieved = repo.get_article_by_id(5001)
    assert retrieved.post_type == "photo"
    assert json.loads(retrieved.related_article_ids) == [5002, 5003]


def test_comments_upsert_and_cascade_delete(session):
    repo = Repository(session)

    art_data = {
        "id": 6001,
        "title": "Bài viết nhiều tranh luận",
        "slug": "bai-viet-nhieu-tranh-luan-6001",
        "description": "Sapo",
        "content_html": "<p>Nội dung</p>",
        "content_text": "Nội dung",
        "origin_url": "https://vnexpress.net/6001.html",
    }
    comments_data = [
        {
            "id": 7001,
            "user_name": "Tran Van B",
            "content": "Tôi đồng tình với quan điểm này",
            "likes": 5,
            "time_str": "2 giờ trước",
            "reply_count": 0,
        },
        {
            "id": 7002,
            "user_name": "Le Thi C",
            "content": "Tôi có ý kiến trái chiều",
            "likes": 42,
            "time_str": "1 giờ trước",
            "reply_count": 3,
        },
    ]

    art = repo.upsert_article(art_data, comments=comments_data)
    assert len(art.comments) == 2

    # Verify get_comments_by_article sorts by likes DESC
    fetched_cmts = repo.get_comments_by_article(6001)
    assert len(fetched_cmts) == 2
    assert fetched_cmts[0].id == 7002
    assert fetched_cmts[0].likes == 42
    assert fetched_cmts[1].id == 7001
    assert fetched_cmts[1].likes == 5

    # Test update existing comment likes
    comments_updated = [
        {
            "id": 7001,
            "likes": 99,
            "reply_count": 1,
        }
    ]
    repo.upsert_article(art_data, comments=comments_updated)
    updated_cmts = repo.get_comments_by_article(6001)
    top_cmt = next(c for c in updated_cmts if c.id == 7001)
    assert top_cmt.likes == 99
    assert top_cmt.reply_count == 1
    assert len(updated_cmts) == 2  # No duplicates created

    # Test save_comments standalone method
    add_count = repo.save_comments(
        6001,
        [
            {
                "id": 7003,
                "user_name": "Pham D",
                "content": "Bình luận mới thêm",
                "likes": 12,
            }
        ],
    )
    assert add_count == 1
    assert len(repo.get_comments_by_article(6001)) == 3

    # Test stats includes total_comments
    stats = repo.get_stats()
    assert stats["total_comments"] == 3

    # Test CASCADE delete
    session.delete(art)
    session.commit()
    assert len(repo.get_comments_by_article(6001)) == 0


def test_api_article_detail_with_phase2_fields(session):
    """Integration test verifying GET /api/articles/{id} returns comments, post_type, and related articles."""
    cat = Category(
        name="Số hóa",
        slug="so-hoa",
        origin_url="https://vnexpress.net/so-hoa",
    )
    session.add(cat)
    session.flush()

    art_main = Article(
        id=8001,
        title="Đánh giá laptop cao cấp 2026",
        slug="danh-gia-laptop-8001",
        description="Mẫu máy mỏng nhẹ",
        content_html="<p>Review chi tiết máy...</p>",
        content_text="Review chi tiết máy...",
        origin_url="https://vnexpress.net/8001.html",
        category_id=cat.id,
        post_type="infographic",
        related_article_ids=json.dumps([8002]),
        published_at=datetime.now(timezone.utc),
    )
    art_related = Article(
        id=8002,
        title="Trên tay điện thoại gập mới",
        slug="tren-tay-dien-thoai-gap-8002",
        description="Điện thoại thiết kế độc đáo",
        content_html="<p>Review điện thoại...</p>",
        content_text="Review điện thoại...",
        origin_url="https://vnexpress.net/8002.html",
        category_id=cat.id,
        post_type="photo",
        published_at=datetime.now(timezone.utc),
    )
    art_fallback = Article(
        id=8003,
        title="Chip xử lý thế hệ mới ra mắt",
        slug="chip-xu-ly-the-he-moi-8003",
        description="Hiệu năng tăng 50%",
        content_html="<p>Chi tiết chip...</p>",
        content_text="Chi tiết chip...",
        origin_url="https://vnexpress.net/8003.html",
        category_id=cat.id,
        post_type="text",
        published_at=datetime.now(timezone.utc),
    )
    session.add_all([art_main, art_related, art_fallback])
    session.flush()

    # Add comments to main article
    cmt1 = Comment(
        id=9001,
        article_id=art_main.id,
        user_name="Cong Nghe Fan",
        content="Máy đẹp quá!",
        likes=10,
        time_str="15 phút trước",
    )
    cmt2 = Comment(
        id=9002,
        article_id=art_main.id,
        user_name="Reviewer Pro",
        content="Giá hơi cao so với cấu hình.",
        likes=85,
        time_str="30 phút trước",
    )
    session.add_all([cmt1, cmt2])
    session.commit()

    # Create TestClient with dependency override
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get(f"/api/v1/articles/{art_main.id}")
    assert response.status_code == 200
    data = response.json()

    # 1. Check post_type
    assert data["post_type"] == "infographic"

    # 2. Check related_article_ids and related_articles
    assert data["related_article_ids"] == [8002]
    related_ids = [r["id"] for r in data["related_articles"]]
    assert 8002 in related_ids
    # Fallback to category fills art 8003
    assert 8003 in related_ids

    # 3. Check comments sorting (highest likes first)
    comments = data["comments"]
    assert len(comments) == 2
    assert comments[0]["id"] == 9002
    assert comments[0]["likes"] == 85
    assert comments[0]["user_name"] == "Reviewer Pro"
    assert comments[1]["id"] == 9001
    assert comments[1]["likes"] == 10

    # 4. Check listing endpoint also includes post_type
    list_resp = client.get("/api/v1/articles")
    assert list_resp.status_code == 200
    list_items = list_resp.json()["items"]
    main_summary = next(item for item in list_items if item["id"] == 8001)
    assert main_summary["post_type"] == "infographic"

    # Cleanup
    app.dependency_overrides.clear()
