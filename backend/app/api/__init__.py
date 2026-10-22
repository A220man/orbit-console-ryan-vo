"""API route definitions."""

from fastapi import APIRouter

from .actors import router as actors_router
from .snapshots import router as snapshots_router
from .telemetry import router as telemetry_router
from .auth import router as auth_router
from .health import router as health_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(actors_router, prefix="/actors", tags=["actors"])
api_router.include_router(snapshots_router, prefix="/actors", tags=["snapshots"])
api_router.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])