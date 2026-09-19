"""Deduplication Engine using Redis Set with automatic Local/Memory fallback."""

import logging
from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Set

from crawler.config import settings

logger = logging.getLogger(__name__)


class Deduplicator(ABC):
    """Abstract interface for checking and marking seen article IDs."""

    @abstractmethod
    def is_seen(self, article_id: int) -> bool:
        """Check if article_id was already seen."""
        pass

    @abstractmethod
    def mark_seen(self, article_id: int) -> bool:
        """Mark article_id as seen. Return True if newly added, False if already seen."""
        pass

    @abstractmethod
    def filter_unseen(self, article_ids: Iterable[int]) -> List[int]:
        """Filter and return only IDs that have not been seen yet."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Count total seen IDs."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all seen records."""
        pass


class RedisDeduplicator(Deduplicator):
    """Deduplication implementation backed by Redis Set (SADD, SISMEMBER)."""

    def __init__(self, redis_url: str = settings.redis_url, key: str = settings.redis_dedup_set_key):
        import redis
        self.key = key
        self.client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        self.client.ping()
        logger.info("Connected to Redis at %s for deduplication set '%s'", redis_url, key)

    def is_seen(self, article_id: int) -> bool:
        return bool(self.client.sismember(self.key, str(article_id)))

    def mark_seen(self, article_id: int) -> bool:
        added = self.client.sadd(self.key, str(article_id))
        return bool(added > 0)

    def filter_unseen(self, article_ids: Iterable[int]) -> List[int]:
        ids = list(article_ids)
        if not ids:
            return []
        pipeline = self.client.pipeline()
        for aid in ids:
            pipeline.sismember(self.key, str(aid))
        results = pipeline.execute()
        return [aid for aid, is_member in zip(ids, results) if not is_member]

    def count(self) -> int:
        return int(self.client.scard(self.key))

    def clear(self) -> None:
        self.client.delete(self.key)


class LocalDeduplicator(Deduplicator):
    """In-memory deduplication implementation for local testing and fallback."""

    def __init__(self, initial_ids: Optional[Iterable[int]] = None):
        self._seen: Set[int] = set(initial_ids) if initial_ids else set()
        logger.info("Using Local Deduplicator (initialized with %d seen IDs)", len(self._seen))

    def is_seen(self, article_id: int) -> bool:
        return article_id in self._seen

    def mark_seen(self, article_id: int) -> bool:
        if article_id in self._seen:
            return False
        self._seen.add(article_id)
        return True

    def filter_unseen(self, article_ids: Iterable[int]) -> List[int]:
        return [aid for aid in article_ids if aid not in self._seen]

    def count(self) -> int:
        return len(self._seen)

    def clear(self) -> None:
        self._seen.clear()


def get_deduplicator(prefer_redis: bool = True, load_from_db: bool = True) -> Deduplicator:
    """Factory to get RedisDeduplicator with automatic fallback to LocalDeduplicator."""
    if prefer_redis:
        try:
            return RedisDeduplicator()
        except Exception as exc:
            logger.warning("Could not connect to Redis (%s). Falling back to LocalDeduplicator.", exc)

    initial_ids = set()
    if load_from_db:
        try:
            from crawler.storage.database import get_db_session
            from crawler.storage.models import Article
            from sqlalchemy import select
            with get_db_session() as session:
                existing_ids = session.execute(select(Article.id)).scalars().all()
                initial_ids = set(existing_ids)
        except Exception as db_exc:
            logger.debug("Could not pre-load seen article IDs from DB: %s", db_exc)

    return LocalDeduplicator(initial_ids=initial_ids)
