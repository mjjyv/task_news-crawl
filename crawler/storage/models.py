"""SQLAlchemy models for VnExpress news articles, categories, media, and crawl logs."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True
    )
    origin_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # VnExpress article ID
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    origin_url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="articles")
    media: Mapped[List["Media"]] = relationship(
        "Media", back_populates="article", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_articles_category_published", "category_id", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title[:30]}...')>"


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'image', 'video'
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    local_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["Article"] = relationship("Article", back_populates="media")

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, article_id={self.article_id}, type='{self.type}')>"


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crawler_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'success', 'failed', 'skipped'
    articles_found: Mapped[int] = mapped_column(Integer, default=0)
    articles_new: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<CrawlLog(id={self.id}, crawler_type='{self.crawler_type}', status='{self.status}')>"
