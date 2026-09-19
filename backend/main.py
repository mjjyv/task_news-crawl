"""FastAPI Main Application Entry Point."""

from contextlib import asynccontextmanager
import logging
import time
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import api_settings
from backend.routers import (
    articles_router,
    categories_router,
    crawler_router,
    search_router,
)
from crawler.storage.database import init_db

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    logger.info("Starting up %s (version: %s)", api_settings.app_name, api_settings.app_version)
    # Ensure all tables exist on startup
    init_db()
    yield
    logger.info("Shutting down %s", api_settings.app_name)


app = FastAPI(
    title=api_settings.app_name,
    version=api_settings.app_version,
    description="RESTful API Backend cho hệ thống tổng hợp & cào tin tức VnExpress tự động.",
    docs_url=api_settings.docs_url,
    redoc_url=api_settings.redoc_url,
    openapi_url=api_settings.openapi_url,
    lifespan=lifespan,
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Process Time Header Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


# 3. Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception at %s %s: %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Đã xảy ra lỗi máy chủ nội bộ. Vui lòng thử lại sau."},
    )


# 4. Include Routers with v1 prefix
app.include_router(
    categories_router,
    prefix=f"{api_settings.api_v1_prefix}/categories",
    tags=["Categories"],
)
app.include_router(
    articles_router,
    prefix=f"{api_settings.api_v1_prefix}/articles",
    tags=["Articles"],
)
app.include_router(
    search_router,
    prefix=f"{api_settings.api_v1_prefix}/search",
    tags=["Search"],
)
app.include_router(
    crawler_router,
    prefix=f"{api_settings.api_v1_prefix}/crawler",
    tags=["Crawler & Monitoring"],
)


@app.get("/", summary="Root API Information", tags=["General"])
def root_info() -> Dict[str, Any]:
    """Thông tin tổng quan về API và các liên kết tài liệu."""
    return {
        "app_name": api_settings.app_name,
        "version": api_settings.app_version,
        "status": "online",
        "documentation": {
            "swagger_ui": api_settings.docs_url,
            "redoc": api_settings.redoc_url,
            "openapi_spec": api_settings.openapi_url,
        },
        "endpoints": {
            "categories": f"{api_settings.api_v1_prefix}/categories",
            "articles": f"{api_settings.api_v1_prefix}/articles",
            "search": f"{api_settings.api_v1_prefix}/search",
            "crawler_health": f"{api_settings.api_v1_prefix}/crawler/health",
            "crawler_trigger": f"{api_settings.api_v1_prefix}/crawler/trigger",
        },
    }


@app.get("/health", summary="Liveness Probe", tags=["General"])
def health_check() -> Dict[str, str]:
    """Kiểm tra phản hồi nhanh (Liveness check)."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
