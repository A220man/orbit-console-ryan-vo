"""Telemetry API endpoints."""

from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict

from ..core.database import get_db
from ..core.auth import get_current_active_user, require_roles, ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN
from ..services.telemetry import (
    get_template_metrics,
    get_actor_telemetry,
    get_actor_status_gauge,
    get_metrics_summary,
    get_crash_count,
)

router = APIRouter()


class MetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_namespace: str
    template_name: str
    container_name: str
    metric_name: str
    metric_type: str
    value: float
    sum_value: float
    count: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    labels: Dict[str, str]
    window_start: str
    window_end: str
    created_at: str


class ActorTelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    actor_uid: str
    actor_name: str
    atespace: str
    signal_type: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    log_level: Optional[str] = None
    log_message: Optional[str] = None
    attributes: Dict[str, Any]
    timestamp: str


class MetricsSummaryResponse(BaseModel):
    actor_status_gauge: List[Dict[str, Any]]
    crash_count: int
    transitions: List[Dict[str, Any]]
    created_count: float
    window_start: str
    window_end: str


@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    metric_name: Optional[str] = None,
    since_hours: int = Query(1, ge=1, le=168),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> List[MetricResponse]:
    """Get aggregated metrics for templates."""
    since = datetime.now(UTC) - timedelta(hours=since_hours)
    metrics = await get_template_metrics(
        db,
        template_namespace=template_namespace,
        template_name=template_name,
        metric_name=metric_name,
        since=since,
        limit=limit,
    )
    return metrics


@router.get("/actors/{actor_id}/telemetry", response_model=List[ActorTelemetryResponse])
async def get_actor_telemetry_endpoint(
    actor_id: int,
    signal_type: Optional[str] = Query(None, pattern="^(trace|log)$"),
    trace_id: Optional[str] = None,
    since_hours: int = Query(1, ge=1, le=168),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> List[ActorTelemetryResponse]:
    """Get per-actor telemetry (traces/logs)."""
    since = datetime.now(UTC) - timedelta(hours=since_hours)
    telemetry = await get_actor_telemetry(
        db,
        actor_id=actor_id,
        signal_type=signal_type,
        trace_id=trace_id,
        since=since,
        limit=limit,
    )
    return telemetry


@router.get("/actors/telemetry", response_model=List[ActorTelemetryResponse])
async def get_telemetry_by_actor_uid(
    actor_uid: str,
    signal_type: Optional[str] = Query(None, pattern="^(trace|log)$"),
    trace_id: Optional[str] = None,
    since_hours: int = Query(1, ge=1, le=168),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> List[ActorTelemetryResponse]:
    """Get per-actor telemetry by actor UID."""
    since = datetime.now(UTC) - timedelta(hours=since_hours)
    telemetry = await get_actor_telemetry(
        db,
        actor_uid=actor_uid,
        signal_type=signal_type,
        trace_id=trace_id,
        since=since,
        limit=limit,
    )
    return telemetry


@router.get("/status-gauge", response_model=List[Dict[str, Any]])
async def get_status_gauge(
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> List[Dict[str, Any]]:
    """Get actor status gauge (ate.actors metric)."""
    return await get_actor_status_gauge(db, template_namespace, template_name)


@router.get("/crash-count")
async def get_crash_count_endpoint(
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> dict:
    """Get actor crash count (ate.actor.crashes metric)."""
    count = await get_crash_count(db, template_namespace, template_name)
    return {"crash_count": count}


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary_endpoint(
    since_hours: int = Query(1, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> MetricsSummaryResponse:
    """Get metrics summary for dashboard."""
    since = datetime.now(UTC) - timedelta(hours=since_hours)
    return await get_metrics_summary(db, since)


@router.get("/ate-actors")
async def get_ate_actors_metric(
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> dict:
    """Get ate.actors gauge in Prometheus format."""
    gauge_data = await get_actor_status_gauge(db, template_namespace, template_name)

    lines = [
        "# HELP ate_actors Number of actors by status and template",
        "# TYPE ate_actors gauge",
    ]
    for g in gauge_data:
        labels = f'status="{g["status"]}",template_namespace="{g["template_namespace"]}",template_name="{g["template_name"]}"'
        lines.append(f'ate_actors{{{labels}}} {g["value"]}')

    return {"metric": "ate_actors", "format": "prometheus", "data": "\n".join(lines)}


@router.get("/ate-actor-crashes")
async def get_ate_actor_crashes_metric(
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)),
) -> dict:
    """Get ate.actor.crashes counter in Prometheus format."""
    count = await get_crash_count(db, template_namespace, template_name)

    lines = [
        "# HELP ate_actor_crashes Total number of actors that have crashed",
        "# TYPE ate_actor_crashes counter",
    ]
    labels = f'template_namespace="{template_namespace or "*"}",template_name="{template_name or "*"}"'
    lines.append(f'ate_actor_crashes{{{labels}}} {count}')

    return {"metric": "ate_actor_crashes", "format": "prometheus", "data": "\n".join(lines)}