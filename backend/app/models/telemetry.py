"""Telemetry models for actor metrics and monitoring."""

from datetime import datetime, UTC
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Integer, BigInteger, Float, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from ..core.database import Base


class TelemetryMetric(Base):
    """Aggregated telemetry metric for an actor template."""

    __tablename__ = "telemetry_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Template identification (bounded cardinality)
    template_namespace: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    template_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    container_name: Mapped[str] = mapped_column(String(255), nullable=False, default="main")

    # Metric info
    metric_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(32), nullable=False)  # counter, gauge, histogram

    # Aggregated values (delta temporality)
    value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sum_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # for histograms
    count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)     # for histograms
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Labels (bounded set)
    labels: Mapped[Dict[str, str]] = mapped_column(SQLiteJSON, default=dict, nullable=False)

    # Time window
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("ix_telemetry_template_metric", "template_namespace", "template_name", "metric_name", "window_start"),
        Index("ix_telemetry_time_window", "window_start", "window_end"),
    )

    def __repr__(self) -> str:
        return f"<TelemetryMetric({self.template_namespace}/{self.template_name} {self.metric_name}={self.value})>"


class ActorTelemetry(Base):
    """Per-actor telemetry record (kept for traces/logs, not metrics)."""

    __tablename__ = "actor_telemetry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("actors.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_uid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    atespace: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # Signal type
    signal_type: Mapped[str] = mapped_column(String(16), nullable=False)  # trace, log

    # Trace/span data
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    span_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    parent_span_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Log data
    log_level: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    log_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Common attributes (bounded for metrics, full for traces/logs)
    attributes: Mapped[Dict[str, Any]] = mapped_column(SQLiteJSON, default=dict, nullable=False)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Relationships
    actor: Mapped["Actor"] = relationship(
        "Actor",
        back_populates="telemetry",
        foreign_keys="ActorTelemetry.actor_id",
    )

    # Indexes
    __table_args__ = (
        Index("ix_actor_telemetry_actor_time", "actor_id", "timestamp"),
        Index("ix_actor_telemetry_trace", "trace_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<ActorTelemetry(actor={self.actor_uid}, type={self.signal_type}, time={self.timestamp})>"