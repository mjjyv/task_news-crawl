"""Pipelines for synchronizing categories and ingesting articles."""

from crawler.pipeline.article_pipeline import ArticlePipeline
from crawler.pipeline.category_sync import CategorySyncPipeline

__all__ = ["CategorySyncPipeline", "ArticlePipeline"]
