from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.errors import PlatformException
from backend.app.db.session import init_db
from backend.app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure logging and verify/create database tables
    setup_logging()
    logger.info("Initializing database metadata...")
    init_db()
    logger.info(f"Platform initialized in {'OFFLINE' if settings.OFFLINE_MODE else 'ONLINE'} mode.")
    yield
    # Shutdown
    logger.info("Shutting down Bitcoin Investigation Platform backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Standardized error handling matching Section 5.22
@app.exception_handler(PlatformException)
async def platform_exception_handler(request: Request, exc: PlatformException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(
        f"Platform exception: {exc.code} - {exc.message}",
        extra={"request_id": req_id, "error_code": exc.code, "details": exc.details},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id,
            }
        },
    )


# Health check endpoint
@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint to verify backend availability."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "offline_mode": settings.OFFLINE_MODE,
    }


# Include V1 REST Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve Frontend Dashboard & Static Assets
import os
from pathlib import Path
from fastapi.responses import FileResponse, Response

FRONTEND_DIR = Path("d:/Bitcoin-Investigation-platform/frontend")
STATIC_DIR = FRONTEND_DIR / "static"

@app.get("/", tags=["frontend"])
def serve_dashboard():
    """Serves the primary Forensic Intelligence Dashboard HTML."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/html")
    return {"message": "Frontend index.html not found"}

@app.get("/static/{file_path:path}", tags=["frontend"])
def serve_static(file_path: str):
    """Serves static CSS and JS assets synchronously without extra async dependencies."""
    target = STATIC_DIR / file_path
    if not target.exists() or not target.is_file():
        return Response(status_code=404, content="File not found")
    media_type = "text/plain"
    if target.suffix == ".css":
        media_type = "text/css"
    elif target.suffix == ".js":
        media_type = "application/javascript"
    elif target.suffix == ".html":
        media_type = "text/html"
    elif target.suffix in (".png", ".jpg", ".jpeg"):
        media_type = f"image/{target.suffix.lstrip('.')}"

    with open(target, "rb") as f:
        return Response(content=f.read(), media_type=media_type)
