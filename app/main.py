import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.exceptions import (
    GestionePalchiException,
    general_exception_handler,
    gestione_palchi_exception_handler,
    integrity_error_handler,
)
from app.database.base import Base, engine

# Import optimized routers
from app.routers import auth, reports
from app.routers.associations import router as associations_router
from app.routers.events import router as events_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level), format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("🚀 Avvio Gestione Palchi API...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelle del database create/verificate")

    yield

    # Shutdown
    logger.info("🔄 Arresto Gestione Palchi API...")


# Create FastAPI app with optimized configuration
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Optimized API for managing municipal stages organized by Pro Loco association",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=86400,  # 24 hours
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        logger.warning(
            f"⚠️ Richiesta lenta: {request.method} {request.url.path} ha richiesto {process_time:.2f}s"
        )

    return response


# Exception handlers
app.add_exception_handler(GestionePalchiException, gestione_palchi_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers with optimized prefix
api_prefix = settings.api_prefix

app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["authentication"])
app.include_router(
    associations_router, prefix=f"{api_prefix}/associations", tags=["associations"]
)
app.include_router(events_router, prefix=f"{api_prefix}/events", tags=["events"])
app.include_router(reports.router, prefix=f"{api_prefix}/reports", tags=["reports"])


# Health check endpoints
@app.get("/")
async def root():
    """Serve the main frontend application."""
    return FileResponse("public/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
    }


# Mount static files and frontend
app.mount("/", StaticFiles(directory="public"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main_optimized:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=settings.debug,
    )
