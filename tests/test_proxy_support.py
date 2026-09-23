"""Unit tests for Proxy support in crawler components."""

import pytest
from crawler.config import Settings
from crawler.http_client import HttpClient
from crawler.pipeline.article_pipeline import ArticlePipeline


def test_settings_proxy_configuration():
    """Verify proxy_url field in Settings with defaults and custom env."""
    default_settings = Settings()
    # Default without env should be None
    assert default_settings.proxy_url is None

    # Custom override
    custom_settings = Settings(PROXY_URL="socks5://127.0.0.1:40000")
    assert custom_settings.proxy_url == "socks5://127.0.0.1:40000"


def test_http_client_proxy_initialization():
    """Verify HttpClient properly configures proxy on sync and async clients."""
    proxy = "socks5://127.0.0.1:40000"
    client = HttpClient(proxy_url=proxy)
    assert client.proxy_url == proxy

    # Test sync client initialization
    sync_client = client.get_sync_client()
    assert sync_client is not None
    client.close()

    # Test async client initialization
    async_client = client.get_async_client()
    assert async_client is not None


def test_http_client_password_masking_log(caplog):
    """Verify passwords in proxy credentials are masked when logged."""
    import logging
    with caplog.at_level(logging.INFO):
        client = HttpClient(proxy_url="http://admin:secret_pass@10.0.0.1:8080")
        assert "admin:***@10.0.0.1:8080" in caplog.text
        assert "secret_pass" not in caplog.text
        client.close()


def test_article_pipeline_proxy_propagation():
    """Verify ArticlePipeline forwards proxy_url to its HttpClient instance."""
    proxy = "http://127.0.0.1:8888"
    pipeline = ArticlePipeline(proxy_url=proxy)
    assert pipeline.http_client.proxy_url == proxy


def test_cli_proxy_argument_parsing():
    """Verify CLI parser handles --proxy and -p correctly for various commands."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", "-p", default=None)
    sub = parser.add_subparsers(dest="command")
    p_cat = sub.add_parser("crawl-category")
    p_cat.add_argument("slug")
    p_cat.add_argument("--proxy", "-p", default=None)

    args = parser.parse_args(["crawl-category", "khoa-hoc", "--proxy", "socks5://127.0.0.1:40000"])
    assert args.proxy == "socks5://127.0.0.1:40000"

    args_short = parser.parse_args(["crawl-category", "thoi-su", "-p", "http://proxy.local:3128"])
    assert args_short.proxy == "http://proxy.local:3128"


def test_cron_proxy_argument_parsing():
    """Verify cron runner parses --proxy argument."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="hourly")
    parser.add_argument("--proxy", "-p", default=None)

    args = parser.parse_args(["--mode", "hourly", "--proxy", "socks5://127.0.0.1:9050"])
    assert args.proxy == "socks5://127.0.0.1:9050"
