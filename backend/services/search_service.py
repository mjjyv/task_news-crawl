"""Full-Text and Multi-field Vietnamese Search Service."""

import math
import re
import unicodedata
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.schemas.article import CategoryShort
from backend.schemas.search import SearchResponse, SearchResultItem
from backend.services.category_service import CategoryService
from crawler.storage.models import Article, Category


def remove_vietnamese_accents(text: str) -> str:
    """Normalize and strip Vietnamese diacritics for accent-insensitive search."""
    if not text:
        return ""
    # Normalize unicode to decomposed form
    text = unicodedata.normalize("NFD", text)
    # Strip non-spacing marks (combining diacritics)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    # Replace đ and Đ
    text = text.replace("đ", "d").replace("Đ", "D")
    return unicodedata.normalize("NFC", text).lower().strip()


class SearchService:
    """Service handling multi-field Vietnamese search with relevance scoring and snippet generation."""

    def __init__(self, session: Session):
        self.session = session
        self.category_service = CategoryService(session)

    def search(
        self,
        query: str,
        category_slug: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """Search articles across title and content with accent-insensitivity."""
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        clean_query = query.strip()

        if not clean_query:
            return SearchResponse(
                query=query,
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                items=[],
            )

        norm_query = remove_vietnamese_accents(clean_query)
        keywords = [kw for kw in norm_query.split() if len(kw) > 1]
        if not keywords:
            keywords = [norm_query]

        # 1. Base query with category filtering
        stmt = select(Article).options(selectinload(Article.category))

        if category_slug:
            cat = self.session.execute(
                select(Category).where(Category.slug == category_slug)
            ).scalar_one_or_none()
            if cat:
                cat_ids = self.category_service.get_descendant_category_ids(cat.id)
                stmt = stmt.where(Article.category_id.in_(cat_ids))
            else:
                return SearchResponse(
                    query=query,
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                    items=[],
                )

        # 2. Filter candidates matching keywords
        filters = [
            Article.title.ilike(f"%{clean_query}%"),
            Article.description.ilike(f"%{clean_query}%"),
            Article.content_text.ilike(f"%{clean_query}%"),
            Article.slug.ilike(f"%{'-'.join(keywords)}%"),
        ]

        dialect_name = self.session.bind.dialect.name if self.session.bind else "sqlite"
        if dialect_name == "sqlite":
            filters.append(func.remove_accents(Article.title).ilike(f"%{norm_query}%"))
            filters.append(func.remove_accents(Article.description).ilike(f"%{norm_query}%"))
            filters.append(func.remove_accents(Article.content_text).ilike(f"%{norm_query}%"))
            for kw in keywords:
                filters.append(func.remove_accents(Article.title).ilike(f"%{kw}%"))
                filters.append(func.remove_accents(Article.description).ilike(f"%{kw}%"))
                filters.append(func.remove_accents(Article.content_text).ilike(f"%{kw}%"))
        else:
            for kw in keywords:
                filters.append(Article.title.ilike(f"%{kw}%"))
                filters.append(Article.description.ilike(f"%{kw}%"))
                filters.append(Article.content_text.ilike(f"%{kw}%"))
                filters.append(Article.slug.ilike(f"%{kw}%"))

        stmt = stmt.where(or_(*filters))

        candidates = self.session.execute(stmt).scalars().all()

        # 3. Score and rank candidates in Python (combines accented & unaccented relevance)
        scored_results: List[Tuple[float, Article, str]] = []
        for art in candidates:
            score, snippet = self._score_article(art, clean_query, norm_query, keywords)
            if score > 0:
                scored_results.append((score, art, snippet))

        # Sort by relevance score desc
        scored_results.sort(key=lambda x: x[0], reverse=True)

        total = len(scored_results)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_candidates = scored_results[start_idx:end_idx]

        items = [
            SearchResultItem(
                id=art.id,
                title=art.title,
                slug=art.slug,
                description=art.description,
                thumbnail_url=art.thumbnail_url,
                author=art.author,
                published_at=art.published_at,
                category=CategoryShort.model_validate(art.category) if art.category else None,
                score=round(score, 2),
                snippet=snippet,
            )
            for score, art, snippet in paged_candidates
        ]

        return SearchResponse(
            query=query,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items,
        )

    def _score_article(
        self,
        art: Article,
        raw_query: str,
        norm_query: str,
        keywords: List[str],
    ) -> Tuple[float, str]:
        score = 0.0

        title_raw = art.title.lower()
        title_norm = remove_vietnamese_accents(art.title)
        desc_norm = remove_vietnamese_accents(art.description or "")
        content_norm = remove_vietnamese_accents(art.content_text or "")

        # 1. Exact full query phrase match
        has_phrase_match = False
        if raw_query.lower() in title_raw:
            score += 50.0
            has_phrase_match = True
        elif norm_query in title_norm:
            score += 40.0
            has_phrase_match = True

        if norm_query in desc_norm:
            score += 20.0
            has_phrase_match = True

        if norm_query in content_norm:
            score += 10.0
            has_phrase_match = True

        # 2. Word-boundary keyword matches
        title_hits = 0
        desc_hits = 0
        content_hits = 0
        matched_words = set()

        for kw in keywords:
            pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
            t_cnt = len(pattern.findall(title_norm))
            d_cnt = len(pattern.findall(desc_norm))
            c_cnt = len(pattern.findall(content_norm))

            if t_cnt > 0:
                title_hits += t_cnt
                matched_words.add(kw)
            if d_cnt > 0:
                desc_hits += d_cnt
                matched_words.add(kw)
            if c_cnt > 0:
                content_hits += c_cnt
                matched_words.add(kw)

        score += title_hits * 10.0
        score += desc_hits * 5.0
        score += min(content_hits * 1.0, 10.0)

        # Qualification filter:
        # If no phrase match, ensure at least half of the query keywords matched as distinct whole words
        min_required = max(1, (len(keywords) + 1) // 2)
        if not has_phrase_match and len(matched_words) < min_required:
            return 0.0, ""

        if score <= 0.0:
            return 0.0, ""

        snippet = self._generate_snippet(art.content_text or art.description or "", keywords)
        return score, snippet

    def _generate_snippet(self, text: str, keywords: List[str], max_len: int = 160) -> str:
        if not text:
            return ""

        norm_text = remove_vietnamese_accents(text)
        best_pos = -1

        for kw in keywords:
            match = re.search(r"\b" + re.escape(kw) + r"\b", norm_text, re.IGNORECASE)
            if match:
                best_pos = match.start()
                break

        if best_pos == -1:
            for kw in keywords:
                idx = norm_text.find(kw)
                if idx != -1:
                    best_pos = idx
                    break

        if best_pos == -1:
            return text[:max_len] + ("..." if len(text) > max_len else "")

        start = max(0, best_pos - 40)
        end = min(len(text), start + max_len)

        # Snap to word boundary
        while start > 0 and text[start] not in (" ", "\n", ".", ","):
            start -= 1
        while end < len(text) and text[end] not in (" ", "\n", ".", ","):
            end += 1

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return prefix + text[start:end].strip() + suffix
