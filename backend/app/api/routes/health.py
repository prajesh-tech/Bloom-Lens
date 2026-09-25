from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.core.metrics import metrics
from app.services.embedding_service import get_embedding_backend_status

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Basic health check endpoint for load balancers and uptime probes."""
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "api_version": "v1",
    }


@router.get("/deep", status_code=status.HTTP_200_OK)
async def deep_health_check(db: AsyncSession = Depends(get_db)):
    """Deep health check endpoint covering database and optional service readiness."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Deep health check database connectivity failed: {e}")
        db_status = "unhealthy"

    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
        "embedding_backend": get_embedding_backend_status(),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "api_version": "v1",
        "metrics": metrics.snapshot(),
    }
