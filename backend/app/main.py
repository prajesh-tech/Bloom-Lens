import time
import uuid
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import ensure_database_schema_current
from app.core.errors import http_exception_handler, validation_exception_handler, unhandled_exception_handler
from app.core.logging import logger
from app.core.metrics import metrics
from app.core.upload_limits import UploadBodyLimitMiddleware
from app.services.paper_processing_service import fail_interrupted_jobs
from app.api.routes import health, papers, questions, analytics, courses, course_outcomes, browser_auth, subjects
from app.services.embedding_service import get_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preloads ML embedding models during application startup to prevent upload freezes."""
    settings.validate_runtime_config()
    await ensure_database_schema_current()
    await fail_interrupted_jobs()
    if settings.WARMUP_EMBEDDING_ON_STARTUP:
        logger.info("Warming up ML SentenceTransformer embedding model on startup...")
        try:
            get_embedding_model()
            logger.info("ML SentenceTransformer model preloaded successfully.")
        except Exception as e:
            logger.warning(f"ML Model warmup warning: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="BloomLens V1 API — AI-Powered Historical Question Paper Analysis System",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(UploadBodyLimitMiddleware)

# Configure CORS Middleware for React Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    supplied_id = request.headers.get("X-Request-ID", "")
    request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._:-]{1,64}", supplied_id) else uuid.uuid4().hex
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Request-ID"] = request_id
    endpoint = getattr(request.scope.get("route"), "path", "__unmatched__")
    if endpoint != '__unmatched__' and request.url.path.startswith(settings.API_V1_STR + '/') and not endpoint.startswith(settings.API_V1_STR + '/'):
        endpoint = settings.API_V1_STR + endpoint
    metrics.record_request(endpoint, process_time, response.status_code)
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "endpoint": endpoint,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
        },
    )
    return response


# Register API Router Endpoints under /api/v1
api_v1_prefix = settings.API_V1_STR
app.include_router(browser_auth.router, prefix=api_v1_prefix)
app.include_router(subjects.router, prefix=api_v1_prefix)
app.include_router(health.router, prefix=api_v1_prefix)
app.include_router(papers.router, prefix=api_v1_prefix)
app.include_router(questions.router, prefix=api_v1_prefix)
app.include_router(analytics.router, prefix=api_v1_prefix)
app.include_router(courses.router, prefix=api_v1_prefix)
app.include_router(course_outcomes.router, prefix=api_v1_prefix)


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }
