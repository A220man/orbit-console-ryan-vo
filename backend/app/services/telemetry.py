"""Telemetry service - metrics collection and querying."""

from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from ..models.telemetry import TelemetryMetric, ActorTelemetry
from ..models.actor import Actor, ActorStatus
from ..core.config import settings


async def record_actor_metric(
    db: AsyncSession,
    template_namespace: str,
    template_name: str,
    container_name: str,
    metric_name: str,
    metric_type: str,
    value: float,
    labels: Optional[Dict[str, str]] = None,
    window_seconds: int = 60,
) -> TelemetryMetric:
    """Record a metric data point (delta temporality)."""
    now = datetime.now(UTC)
    window_start = now - timedelta(seconds=window_seconds)
    window_start = window_start.replace(second=0, microsecond=0)
    window_end = window_start + timedelta(seconds=window_seconds)

    # Find existing metric in current window
    query = select(TelemetryMetric).where(
        and_(
            TelemetryMetric.template_namespace == template_namespace,
            TelemetryMetric.template_name == template_name,
            TelemetryMetric.container_name == container_name,
            TelemetryMetric.metric_name == metric_name,
            TelemetryMetric.metric_type == metric_type,
            TelemetryMetric.window_start == window_start,
        )
    )
    if labels:
        # Note: JSON comparison in SQLite is limited; we store labels but query by core dims
        pass

    result = await db.execute(query)
    metric = result.scalar_one_or_none()

    if metric:
        # Update existing (delta: add to value)
        if metric_type == "counter":
            metric.value += value
            metric.sum_value += value
            metric.count += 1
        elif metric_type == "gauge":
            # Gauge: last write wins (but we track min/max)
            metric.value = value
            metric.sum_value += value
            metric.count += 1
            if metric.min_value is None or value < metric.min_value:
                metric.min_value = value
            if metric.max_value is None or value > metric.max_value:
                metric.max_value = value
        elif metric_type == "histogram":
            metric.sum_value += value
            metric.count += 1
            if metric.min_value is None or value < metric.min_value:
                metric.min_value = value
            if metric.max_value is None or value > metric.max_value:
                metric.max_value = value
        metric.updated_at = now
    else:
        # Create new
        metric = TelemetryMetric(
            template_namespace=template_namespace,
            template_name=template_name,
            container_name=container_name,
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            sum_value=value,
            count=1,
            min_value=value,
            max_value=value,
            labels=labels or {},
            window_start=window_start,
            window_end=window_end,
        )
        db.add(metric)

    await db.flush()
    await db.refresh(metric)
    return metric


async def record_actor_telemetry(
    db: AsyncSession,
    actor_id: int,
    actor_uid: str,
    actor_name: str,
    atespace: str,
    signal_type: str,  # "trace" or "log"
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    log_level: Optional[str] = None,
    log_message: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> ActorTelemetry:
    """Record per-actor telemetry (traces/logs)."""
    telemetry = ActorTelemetry(
        actor_id=actor_id,
        actor_uid=actor_uid,
        actor_name=actor_name,
        atespace=atespace,
        signal_type=signal_type,
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        log_level=log_level,
        log_message=log_message,
        attributes=attributes or {},
    )
    db.add(telemetry)
    await db.flush()
    await db.refresh(telemetry)
    return telemetry


async def get_template_metrics(
    db: AsyncSession,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    metric_name: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 1000,
) -> List[TelemetryMetric]:
    """Get aggregated metrics for templates."""
    query = select(TelemetryMetric)

    conditions = []
    if template_namespace:
        conditions.append(TelemetryMetric.template_namespace == template_namespace)
    if template_name:
        conditions.append(TelemetryMetric.template_name == template_name)
    if metric_name:
        conditions.append(TelemetryMetric.metric_name == metric_name)
    if since:
        conditions.append(TelemetryMetric.window_start >= since)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(TelemetryMetric.window_start.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_actor_telemetry(
    db: AsyncSession,
    actor_id: Optional[int] = None,
    actor_uid: Optional[str] = None,
    signal_type: Optional[str] = None,
    trace_id: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 1000,
) -> List[ActorTelemetry]:
    """Get per-actor telemetry (traces/logs)."""
    query = select(ActorTelemetry)

    conditions = []
    if actor_id:
        conditions.append(ActorTelemetry.actor_id == actor_id)
    if actor_uid:
        conditions.append(ActorTelemetry.actor_uid == actor_uid)
    if signal_type:
        conditions.append(ActorTelemetry.signal_type == signal_type)
    if trace_id:
        conditions.append(ActorTelemetry.trace_id == trace_id)
    if since:
        conditions.append(ActorTelemetry.timestamp >= since)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(ActorTelemetry.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_actor_count_by_status(
    db: AsyncSession,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
) -> Dict[str, int]:
    """Get actor count grouped by status (for ate.actors gauge)."""
    from ..services.actor import get_actor_count_by_status as _get_actor_count_by_status
    return await _get_actor_count_by_status(db, template_namespace, template_name)


async def get_crash_count(
    db: AsyncSession,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
) -> int:
    """Get count of actors in CRASHED state (for ate.actor.crashes metric)."""
    from ..services.actor import get_crash_count as _get_crash_count
    return await _get_crash_count(db, template_namespace, template_name)


async def get_actor_status_gauge(
    db: AsyncSession,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get actor status gauge data for Prometheus-style output."""
    counts = await get_actor_count_by_status(db, template_namespace, template_name)

    result = []
    for status in ["running", "paused", "suspended", "crashed"]:
        result.append({
            "metric": "ate_actors",
            "status": status,
            "template_namespace": template_namespace or "*",
            "template_name": template_name or "*",
            "value": counts.get(status, 0),
        })
    return result


async def get_metrics_summary(
    db: AsyncSession,
    since: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get summary of all metrics for dashboard."""
    if not since:
        since = datetime.now(UTC) - timedelta(hours=1)

    # Actor counts by status
    status_gauge = await get_actor_status_gauge(db)

    # Crash count
    crash_count = await get_crash_count(db)

    # Recent transitions
    transitions = await get_template_metrics(
        db, metric_name="ate.actor.transitions", since=since, limit=100
    )

    # Created count
    created = await get_template_metrics(
        db, metric_name="ate.actors.created", since=since, limit=100
    )

    return {
        "actor_status_gauge": status_gauge,
        "crash_count": crash_count,
        "transitions": [
            {
                "template": f"{t.template_namespace}/{t.template_name}",
                "from": t.labels.get("from", "unknown"),
                "to": t.labels.get("to", "unknown"),
                "count": t.value,
            }
            for t in transitions
        ],
        "created_count": sum(c.value for c in created),
        "window_start": since.isoformat(),
        "window_end": datetime.now(UTC).isoformat(),
    }