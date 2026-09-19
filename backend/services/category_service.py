"""Category business logic service."""

from typing import Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.schemas.category import CategoryBase, CategoryDetailResponse, CategoryTreeItem
from crawler.storage.models import Article, Category


class CategoryService:
    """Service handling category hierarchy and statistics."""

    def __init__(self, session: Session):
        self.session = session

    def get_categories(self, tree: bool = True) -> List[CategoryTreeItem]:
        """Fetch categories as tree hierarchy or flat list."""
        if tree:
            return self.get_category_tree()

        categories = self.session.execute(select(Category).order_by(Category.name)).scalars().all()
        count_stmt = select(Article.category_id, func.count(Article.id)).group_by(Article.category_id)
        counts_map: Dict[int, int] = dict(self.session.execute(count_stmt).all())

        return [
            CategoryTreeItem(
                id=c.id,
                name=c.name,
                slug=c.slug,
                origin_url=c.origin_url,
                parent_id=c.parent_id,
                description=c.description,
                children=[],
                article_count=counts_map.get(c.id, 0),
            )
            for c in categories
        ]

    def get_category_tree(self) -> List[CategoryTreeItem]:
        """Build full recursive category tree with article counts."""
        # 1. Fetch all categories
        categories = self.session.execute(select(Category).order_by(Category.name)).scalars().all()

        # 2. Get article count per category
        count_stmt = select(Article.category_id, func.count(Article.id)).group_by(Article.category_id)
        counts_map: Dict[int, int] = dict(self.session.execute(count_stmt).all())

        # 3. Build tree
        cat_dict: Dict[int, CategoryTreeItem] = {}
        for c in categories:
            cat_dict[c.id] = CategoryTreeItem(
                id=c.id,
                name=c.name,
                slug=c.slug,
                origin_url=c.origin_url,
                parent_id=c.parent_id,
                description=c.description,
                children=[],
                article_count=counts_map.get(c.id, 0),
            )

        tree: List[CategoryTreeItem] = []
        for c in categories:
            item = cat_dict[c.id]
            if c.parent_id and c.parent_id in cat_dict:
                cat_dict[c.parent_id].children.append(item)
            else:
                tree.append(item)

        # 4. Roll up article counts to parent categories
        for root in tree:
            self._rollup_counts(root)

        return tree

    def _rollup_counts(self, item: CategoryTreeItem) -> int:
        child_counts = sum(self._rollup_counts(child) for child in item.children)
        item.article_count += child_counts
        return item.article_count

    def get_category_by_slug(self, slug: str) -> Optional[CategoryDetailResponse]:
        """Get single category with parent, direct children, and article count."""
        stmt = select(Category).where(Category.slug == slug)
        cat = self.session.execute(stmt).scalar_one_or_none()
        if not cat:
            return None

        # Article count (including descendant categories)
        descendant_ids = self.get_descendant_category_ids(cat.id)
        count_stmt = select(func.count(Article.id)).where(Article.category_id.in_(descendant_ids))
        total_articles = self.session.execute(count_stmt).scalar() or 0

        parent_dto = CategoryBase.model_validate(cat.parent) if cat.parent else None
        children_dtos = [CategoryBase.model_validate(ch) for ch in cat.children]

        return CategoryDetailResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            origin_url=cat.origin_url,
            parent_id=cat.parent_id,
            description=cat.description,
            parent=parent_dto,
            children=children_dtos,
            article_count=total_articles,
        )

    def get_descendant_category_ids(self, category_id: int) -> List[int]:
        """Return list of category_id and all its recursive children IDs."""
        result = [category_id]
        stmt = select(Category.id).where(Category.parent_id == category_id)
        children_ids = self.session.execute(stmt).scalars().all()
        for ch_id in children_ids:
            result.extend(self.get_descendant_category_ids(ch_id))
        return result
