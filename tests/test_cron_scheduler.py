"""Unit tests for the Weekly Cronjob Scheduler and Category Batch Runner."""

from unittest.mock import MagicMock, patch
import pytest

from crawler.cron import (
    TOP_RSS_FEEDS,
    WEEKLY_SCHEDULE,
    crawl_100_latest,
    crawl_category_batch,
    get_current_day_key,
    main_cli,
    run_daily_job,
)
from crawler.storage.database import get_db_session, init_db
from crawler.storage.models import Category
from crawler.storage.repository import Repository


def test_weekly_schedule_covers_all_categories():
    """Verify that WEEKLY_SCHEDULE accounts for all 17 parent categories in the database."""
    init_db()
    with get_db_session() as session:
        repo = Repository(session)
        all_cats = repo.get_all_categories()
        db_parent_slugs = {c.slug for c in all_cats if c.parent_id is None}

    scheduled_parent_slugs = set()
    total_slots = 0
    for day_code, info in WEEKLY_SCHEDULE.items():
        assert "name" in info
        assert "slots" in info
        for slot_code, s_data in info["slots"].items():
            total_slots += 1
            assert "time" in s_data
            assert "desc" in s_data
            assert "parents" in s_data
            scheduled_parent_slugs.update(s_data["parents"])

    # All 17 parent slugs from database must be scheduled
    assert db_parent_slugs == scheduled_parent_slugs
    assert len(scheduled_parent_slugs) == 17
    # Exactly 16 slots across the 7 days
    assert total_slots >= 14


def test_get_current_day_key():
    """Check that current day key is valid."""
    day = get_current_day_key()
    assert day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


@patch("crawler.cron.ArticlePipeline")
def test_crawl_100_latest(mock_pipeline_cls):
    """Verify crawl_100_latest queries RSS feeds until 100 articles are fetched."""
    mock_pipeline = MagicMock()
    mock_pipeline_cls.return_value = mock_pipeline

    # Feed 1 returns 40 new, Feed 2 returns 60 new -> total 100
    mock_pipeline.crawl_rss.side_effect = [
        {"articles_found": 45, "articles_new": 40},
        {"articles_found": 65, "articles_new": 60},
    ]

    res = crawl_100_latest(max_articles=100)
    assert res["articles_new"] == 100
    assert res["articles_found"] == 110
    assert mock_pipeline.crawl_rss.call_count == 2


@patch("crawler.cron.ArticlePipeline")
def test_crawl_category_batch(mock_pipeline_cls):
    """Verify crawl_category_batch crawls both parent and child categories independently."""
    mock_pipeline = MagicMock()
    mock_pipeline_cls.return_value = mock_pipeline
    mock_pipeline.crawl_category.return_value = {"articles_found": 10, "articles_new": 5}

    init_db()
    with get_db_session() as session:
        repo = Repository(session)
        # Test with a known parent with 6 children (e.g. thoi-su)
        thoi_su = repo.get_category_by_slug("thoi-su")
        assert thoi_su is not None
        children = repo.get_subcategories(thoi_su.id)
        expected_calls = 1 + len(children)  # 1 parent + children

    result = crawl_category_batch(
        parent_slugs=["thoi-su"],
        max_articles_per_cat=50,
        max_pages=3,
        delay_between_cats=0.0,
    )

    assert result["categories_processed"] == expected_calls
    assert mock_pipeline.crawl_category.call_count == expected_calls


@patch("crawler.cron.crawl_category_batch")
def test_run_daily_job_specific_slot(mock_crawl_batch):
    """Verify run_daily_job executes only the requested slot if specified."""
    run_daily_job(day_key="mon", slot_key="slot1", max_articles=80, max_pages=5)

    assert mock_crawl_batch.call_count == 1
    call_kwargs = mock_crawl_batch.call_args.kwargs
    assert call_kwargs["parent_slugs"] == ["thoi-su"]
    assert call_kwargs["max_articles_per_cat"] == 80
    assert call_kwargs["max_pages"] == 5


@patch("crawler.cron.print_weekly_plan")
def test_main_cli_routing(mock_print_plan):
    """Verify main_cli properly dispatches commands."""
    args = MagicMock()
    args.mode = "schedule"
    main_cli(args)
    mock_print_plan.assert_called_once()
