"""Telemetry service tests."""

import pytest
from datetime import datetime, UTC, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.actor import Actor, ActorStatus
from app.models.telemetry import TelemetryMetric, ActorTelemetry
from app.services.telemetry import (
    record_actor_metric,
    record_actor_telemetry,
    get_template_metrics,
    get_actor_telemetry,
    get_actor_status_gauge,
    get_crash_count,
    get_metrics_summary,
)
from app.services.actor import create_actor, transition_actor_state


@pytest.mark.asyncio
async def test_record_counter_metric(test_session: AsyncSession):
    """Test recording counter metric (delta temporality)."""
    m1 = await record_actor_metric(
        test_session,
        template_namespace="ns1",
        template_name="template-a",
        container_name="main",
        metric_name="test.counter",
        metric_type="counter",
        value=5.0,
    )

    assert m1.value == 5.0
    assert m1.sum_value == 5.0
    assert m1.count == 1

    # Record another in same window - should accumulate
    m2 = await record_actor_metric(
        test_session,
        template_namespace="ns1",
        template_name="template-a",
        container_name="main",
        metric_name="test.counter",
        metric_type="counter",
        value=3.0,
    )

    assert m2.value == 8.0  # 5 + 3
    assert m2.sum_value == 8.0
    assert m2.count == 2


@pytest.mark.asyncio
async def test_record_gauge_metric(test_session: AsyncSession):
    """Test recording gauge metric (last write wins)."""
    m1 = await record_actor_metric(
        test_session,
        template_namespace="ns1",
        template_name="template-a",
        container_name="main",
        metric_name="test.gauge",
        metric_type="gauge",
        value=10.0,
    )

    assert m1.value == 10.0
    assert m1.min_value == 10.0
    assert m1.max_value == 10.0

    # Update gauge
    m2 = await record_actor_metric(
        test_session,
        template_namespace="ns1",
        template_name="template-a",
        container_name="main",
        metric_name="test.gauge",
        metric_type="gauge",
        value=20.0,
    )

    assert m2.value == 20.0  # Last write wins
    assert m2.min_value == 10.0
    assert m2.max_value == 20.0


@pytest.mark.asyncio
async def test_record_histogram_metric(test_session: AsyncSession):
    """Test recording histogram metric."""
    m1 = await record_actor_metric(
        test_session,
        template_namespace="ns1",
        template_name="template-a",
        container_name="main",
        metric_name="test.histogram",
        metric_type="histogram",
        value=100.0,
    )

    assert m1.sum_value == 100.0
    assert m1.count == 1
    assert m1.min_value == 100.0
    assert m1.max_value == 100.0

    m2 = await record_actor_metric(
        test_session,
        template_namespace="ns1",
        template_name="template-a",
        container_name="main",
        metric_name="test.histogram",
        metric_type="histogram",
        value=200.0,
    )

    assert m2.sum_value == 300.0
    assert m2.count == 2
    assert m2.min_value == 100.0
    assert m2.max_value == 200.0


@pytest.mark.asyncio
async def test_record_actor_telemetry(test_session: AsyncSession):
    """Test recording per-actor telemetry (traces/logs)."""
    # Create actor first
    actor = await create_actor(
        test_session,
        uid="telemetry-actor",
        name="Telemetry Actor",
        atespace="default",
        template_namespace="ns1",
        template_name="template-a",
    )

    # Record trace
    trace = await record_actor_telemetry(
        test_session,
        actor_id=actor.id,
        actor_uid=actor.uid,
        actor_name=actor.name,
        atespace=actor.atespace,
        signal_type="trace",
        trace_id="trace-123",
        span_id="span-456",
        parent_span_id="span-789",
        attributes={"http.method": "GET", "http.url": "/api/test"},
    )

    assert trace.id is not None
    assert trace.signal_type == "trace"
    assert trace.trace_id == "trace-123"

    # Record log
    log = await record_actor_telemetry(
        test_session,
        actor_id=actor.id,
        actor_uid=actor.uid,
        actor_name=actor.name,
        atespace=actor.atespace,
        signal_type="log",
        log_level="INFO",
        log_message="Actor started",
        attributes={"component": "runtime"},
    )

    assert log.signal_type == "log"
    assert log.log_level == "INFO"
    assert log.log_message == "Actor started"


@pytest.mark.asyncio
async def test_get_template_metrics(test_session: AsyncSession):
    """Test querying template metrics."""
    # Record some metrics
    await record_actor_metric(test_session, "ns1", "t1", "main", "m1", "counter", 1.0)
    await record_actor_metric(test_session, "ns1", "t1", "main", "m2", "gauge", 5.0)
    await record_actor_metric(test_session, "ns2", "t2", "main", "m1", "counter", 2.0)

    # Query all
    metrics = await get_template_metrics(test_session)
    assert len(metrics) == 3

    # Filter by namespace
    metrics = await get_template_metrics(test_session, template_namespace="ns1")
    assert len(metrics) == 2
    assert all(m.template_namespace == "ns1" for m in metrics)

    # Filter by metric name
    metrics = await get_template_metrics(test_session, metric_name="m1")
    assert len(metrics) == 2
    assert all(m.metric_name == "m1" for m in metrics)


@pytest.mark.asyncio
async def test_get_actor_telemetry(test_session: AsyncSession):
    """Test querying per-actor telemetry."""
    actor = await create_actor(
        test_session,
        uid="telemetry-query",
        name="Telemetry Query",
        atespace="default",
        template_namespace="ns1",
        template_name="template-a",
    )

    await record_actor_telemetry(
        test_session, actor.id, actor.uid, actor.name, actor.atespace,
        "trace", trace_id="t1", span_id="s1"
    )
    await record_actor_telemetry(
        test_session, actor.id, actor.uid, actor.name, actor.atespace,
        "log", log_level="INFO", log_message="test"
    )

    # Query all
    telemetry = await get_actor_telemetry(test_session, actor_id=actor.id)
    assert len(telemetry) == 2

    # Filter by signal type
    traces = await get_actor_telemetry(test_session, actor_id=actor.id, signal_type="trace")
    assert len(traces) == 1
    assert traces[0].signal_type == "trace"

    logs = await get_actor_telemetry(test_session, actor_id=actor.id, signal_type="log")
    assert len(logs) == 1
    assert logs[0].signal_type == "log"


@pytest.mark.asyncio
async def test_actor_status_gauge(test_session: AsyncSession):
    """Test ate.actors gauge data."""
    await create_actor(test_session, uid="g1", name="G1", atespace="s", template_namespace="ns", template_name="t")
    await create_actor(test_session, uid="g2", name="G2", atespace="s", template_namespace="ns", template_name="t")

    actors, _ = await list_actors(test_session)
    await transition_actor_state(test_session, actors[0].id, ActorStatus.RUNNING)
    await transition_actor_state(test_session, actors[1].id, ActorStatus.RUNNING)
    await transition_actor_state(test_session, actors[1].id, ActorStatus.PAUSED)

    gauge = await get_actor_status_gauge(test_session, "ns", "t")
    assert len(gauge) == 4  # running, paused, suspended, crashed

    running = next(g for g in gauge if g["status"] == "running")
    assert running["value"] == 1

    paused = next(g for g in gauge if g["status"] == "paused")
    assert paused["value"] == 1

    suspended = next(g for g in gauge if g["status"] == "suspended")
    assert suspended["value"] == 0


@pytest.mark.asyncio
async def test_crash_count(test_session: AsyncSession):
    """Test ate.actor.crashes counter."""
    await create_actor(test_session, uid="cr1", name="CR1", atespace="s", template_namespace="ns", template_name="t")
    await create_actor(test_session, uid="cr2", name="CR2", atespace="s", template_namespace="ns", template_name="t")

    actors, _ = await list_actors(test_session)
    await transition_actor_state(test_session, actors[0].id, ActorStatus.RUNNING)
    await transition_actor_state(test_session, actors[0].id, ActorStatus.CRASHED)

    count = await get_crash_count(test_session, "ns", "t")
    assert count == 1


@pytest.mark.asyncio
async def test_metrics_summary(test_session: AsyncSession):
    """Test metrics summary for dashboard."""
    await create_actor(test_session, uid="s1", name="S1", atespace="s", template_namespace="ns", template_name="t")
    actors, _ = await list_actors(test_session)
    await transition_actor_state(test_session, actors[0].id, ActorStatus.RUNNING)

    summary = await get_metrics_summary(test_session)
    assert "actor_status_gauge" in summary
    assert "crash_count" in summary
    assert "transitions" in summary
    assert "created_count" in summary
    assert summary["crash_count"] == 0


# Need to import list_actors for tests above
from app.services.actor import list_actors