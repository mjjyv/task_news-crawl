"""Application configuration using Pydantic Settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(default="sqlite:///news.db", alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_dedup_set_key: str = "vnexpress:seen_article_ids"

    # Crawler settings
    base_url: str = Field(default="https://vnexpress.net", alias="BASE_URL")
    rss_base_url: str = Field(default="https://vnexpress.net/rss", alias="RSS_BASE_URL")
    download_delay_min: float = Field(default=0.5, alias="DOWNLOAD_DELAY_MIN")
    download_delay_max: float = Field(default=1.0, alias="DOWNLOAD_DELAY_MAX")
    request_timeout: float = Field(default=15.0, alias="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    concurrent_requests: int = Field(default=5, alias="CONCURRENT_REQUESTS")

    # Media settings
    save_media_local: bool = Field(default=False, alias="SAVE_MEDIA_LOCAL")
    media_storage_dir: str = Field(default="./data/media", alias="MEDIA_STORAGE_DIR")

    # User Agent Pool
    user_agents: List[str] = [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.6; rv:130.0) Gecko/20100101 Firefox/130.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    ]


settings = Settings()
