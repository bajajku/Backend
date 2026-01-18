"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.routers import generate

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context manager."""
    settings = get_settings()
    logger.info(
        "application_started",
        version="1.0.0",
        cors_origins=settings.cors_origins,
        max_file_size_mb=settings.max_file_size_mb,
    )
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Doc-to-3D Explorer API",
        description=(
            "Transform documents into self-contained, interactive 3D HTML experiences "
            "with AI-generated narration. Accessibility-focused for cognitive and "
            "neuro-diverse users."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(generate.router)

    # Serve local models in local mode
    local_models_path = Path(settings.local_models_path)
    if local_models_path.exists():
        app.mount("/static", StaticFiles(directory=str(local_models_path)), name="static")
        logger.info("static_files_mounted", path=str(local_models_path))

    return app


# Create app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Doc-to-3D Explorer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
