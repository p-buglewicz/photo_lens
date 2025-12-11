from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.core import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="LensAnalytics API",
        description="Self-hosted photo analytics engine with local ML embeddings",
        version="0.1.0",
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)

    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 LensAnalytics backend starting up...")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 LensAnalytics backend shutting down...")

    return app


app = create_app()
