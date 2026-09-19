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


def has_vietnamese_accents(text: str) -> bool:
    """Check whether a text contains Vietnamese diacritics / accents."""
    return remove_vietnamese_accents(text) != text.lower()


class SearchService:
    """Service handling multi-field Vietnamese search with relevance scoring and snippet generation."""

    def __init__(self, session: Session):
        self.session = session
        self.category_service = CategoryService(session)

    def search(
        self,
        query: str,
        category_slug: Optional[str] = None,
        exact_accent: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """
        Search articles across title and content.

        - exact_accent=False (default): Accent-insensitive search (e.g. 'tri tue' matches 'trí tuệ').
        - exact_accent=True: Strict accent matching only (e.g. 'ngủ' matches only 'ngủ', not 'ngũ' or 'ngu').
        """
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        clean_query = query.strip()

        if not clean_query:
            return SearchResponse(
                query=query,
                exact_accent=exact_accent,
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
                    exact_accent=exact_accent,
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                    items=[],
                )

        # 2. Filter candidates in database
        if exact_accent:
            # Exact accent mode: match directly against accented text columns
            filters = [
                Article.title.ilike(f"%{clean_query}%"),
                Article.description.ilike(f"%{clean_query}%"),
                Article.content_text.ilike(f"%{clean_query}%"),
            ]
            for rw in clean_query.split():
                if len(rw) > 1:
                    filters.append(Article.title.ilike(f"%{rw}%"))
                    filters.append(Article.description.ilike(f"%{rw}%"))
                    filters.append(Article.content_text.ilike(f"%{rw}%"))
        else:
            # Accent-insensitive mode
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

        # 3. Score and rank candidates in Python
        scored_results: List[Tuple[float, Article, str]] = []
        for art in candidates:
            score, snippet = self._score_article(art, clean_query, norm_query, keywords, exact_accent=exact_accent)
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
            exact_accent=exact_accent,
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
        exact_accent: bool = False,
    ) -> Tuple[float, str]:
        score = 0.0

        title_raw = art.title.lower()
        desc_raw = (art.description or "").lower()
        content_raw = (art.content_text or "").lower()

        title_norm = remove_vietnamese_accents(art.title)
        desc_norm = remove_vietnamese_accents(art.description or "")
        content_norm = remove_vietnamese_accents(art.content_text or "")

        raw_words = [re.sub(r"^[^\w]+|[^\w]+$", "", w).lower() for w in raw_query.split() if w]
        raw_words = [w for w in raw_words if w]
        norm_words = [remove_vietnamese_accents(w) for w in raw_words]

        if exact_accent:
            target_words = raw_words
            t_text, d_text, c_text = title_raw, desc_raw, content_raw
        else:
            target_words = norm_words
            t_text, d_text, c_text = title_norm, desc_norm, content_norm

        valid_kws = [k for k in target_words if len(k) > 1]
        if not valid_kws:
            valid_kws = target_words
        n_kws = len(valid_kws)

        # 1. Exact phrase match with WORD BOUNDARY (prevents substring issues like 'ngu' in 'nguoi')
        phrase_pattern = re.compile(r"\b" + r"\s+".join(re.escape(w) for w in target_words) + r"\b", re.IGNORECASE)
        phrase_in_title = bool(phrase_pattern.search(t_text))
        phrase_in_desc = bool(phrase_pattern.search(d_text))
        phrase_in_content = bool(phrase_pattern.search(c_text))
        has_phrase_match = phrase_in_title or phrase_in_desc or phrase_in_content

        if phrase_in_title:
            score += 60.0
        if phrase_in_desc:
            score += 30.0
        if phrase_in_content:
            score += 20.0

        # 2. Individual keyword matching with word boundaries
        matched_words = set()
        for w in target_words:
            if len(w) <= 1:
                continue
            pat = re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE)
            t_cnt = len(pat.findall(t_text))
            d_cnt = len(pat.findall(d_text))
            c_cnt = len(pat.findall(c_text))

            if t_cnt > 0:
                score += min(t_cnt * 10.0, 20.0)
                matched_words.add(w)
            if d_cnt > 0:
                score += min(d_cnt * 5.0, 10.0)
                matched_words.add(w)
            if c_cnt > 0:
                score += min(c_cnt * 1.0, 10.0)
                matched_words.add(w)

        # 3. Qualification filter:
        if n_kws == 1:
            if len(matched_words) < 1 and not has_phrase_match:
                return 0.0, ""
        elif n_kws == 2:
            # Multi-word: both words must match OR exact phrase match
            if not has_phrase_match and len(matched_words) < 2:
                return 0.0, ""
        else:
            # >= 3 words: phrase match OR at least n_kws - 1 keywords match
            if not has_phrase_match and len(matched_words) < max(2, n_kws - 1):
                return 0.0, ""

        if score <= 0.0:
            return 0.0, ""

        snippet = self._generate_snippet(art, valid_kws, raw_query if exact_accent else norm_query, exact_accent=exact_accent)
        return score, snippet

    def _generate_snippet(self, art: Article, keywords: List[str], target_query: str, exact_accent: bool = False, max_len: int = 160) -> str:
        # Build clean single-spaced text from title, description and content
        full_text = f"{art.title}. {art.description or ''} {art.content_text or ''}"
        clean_text = re.sub(r"\s+", " ", full_text).strip()
        search_text = clean_text if exact_accent else remove_vietnamese_accents(clean_text)
        query_needle = target_query.strip() if exact_accent else remove_vietnamese_accents(target_query.strip())

        best_pos = search_text.lower().find(query_needle.lower())
        if best_pos == -1:
            for kw in keywords:
                m = re.search(r"\b" + re.escape(kw) + r"\b", search_text, re.IGNORECASE)
                if m:
                    best_pos = m.start()
                    break

        if best_pos == -1:
            return clean_text[:max_len] + ("..." if len(clean_text) > max_len else "")

        start = max(0, best_pos - 40)
        end = min(len(clean_text), start + max_len)

        # Snap to word boundary
        while start > 0 and clean_text[start] not in (" ", ".", ","):
            start -= 1
        while end < len(clean_text) and clean_text[end] not in (" ", ".", ","):
            end += 1

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(clean_text) else ""
        return prefix + clean_text[start:end].strip() + suffix
