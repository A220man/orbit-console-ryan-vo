"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..core.database import get_db
from ..core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Basic health check."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness check with database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": settings.app_name,
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "not ready",
            "service": settings.app_name,
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/health/live")
async def liveness_check() -> dict:
    """Liveness check."""
    return {"status": "alive", "service": settings.app_name}