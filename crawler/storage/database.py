"""Database engine, session management, and schema initialization."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

import unicodedata
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from crawler.config import settings
from crawler.storage.models import Base

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def remove_vietnamese_accents(text: str) -> str:
    """Normalize and strip Vietnamese diacritics for accent-insensitive search."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return unicodedata.normalize("NFC", text).lower().strip()


@event.listens_for(Engine, "connect")
def register_sqlite_functions(dbapi_con, connection_record):
    """Register custom SQLite functions on every new SQLite connection."""
    if hasattr(dbapi_con, "create_function"):
        try:
            dbapi_con.create_function("remove_accents", 1, remove_vietnamese_accents)
        except Exception:
            pass


def get_engine(db_url: Optional[str] = None) -> Engine:
    """Get or create the SQLAlchemy engine."""
    global _engine, _SessionFactory
    url = db_url or settings.database_url
    if _engine is None or str(_engine.url) != url:
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(url, echo=False, connect_args=connect_args)
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
        logger.info("Database engine initialized with URL: %s", url.split("@")[-1] if "@" in url else url)
    return _engine


def init_db(engine: Optional[Engine] = None) -> None:
    """Initialize database tables according to the models."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database tables initialized successfully.")


@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    global _SessionFactory
    if _SessionFactory is None:
        get_engine()
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
