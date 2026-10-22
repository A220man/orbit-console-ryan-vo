"""Actor models - core domain entities."""

import enum
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from sqlalchemy import String, DateTime, Boolean, Text, JSON, Integer, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from ..core.database import Base


class ActorStatus(str, enum.Enum):
    """Actor lifecycle states."""
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    CRASHED = "CRASHED"


class SnapshotScope(str, enum.Enum):
    """Snapshot scope: full (memory + fs) or data (durabledir only)."""
    FULL = "full"
    DATA = "data"


class Actor(Base):
    """Actor entity representing a Substrate actor."""

    __tablename__ = "actors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    atespace: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    template_namespace: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    template_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    container_name: Mapped[str] = mapped_column(String(255), nullable=False, default="main")

    status: Mapped[ActorStatus] = mapped_column(
        SQLEnum(ActorStatus), default=ActorStatus.SUSPENDED, nullable=False, index=True
    )
    snapshot_scope: Mapped[SnapshotScope] = mapped_column(
        SQLEnum(SnapshotScope), default=SnapshotScope.DATA, nullable=False
    )

    # Node/worker assignment
    node_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Snapshot references
    latest_snapshot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("snapshots.id"), nullable=True)
    paused_snapshot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("snapshots.id"), nullable=True)

    # Metadata
    labels: Mapped[Dict[str, str]] = mapped_column(SQLiteJSON, default=dict, nullable=False)
    annotations: Mapped[Dict[str, str]] = mapped_column(SQLiteJSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )
    last_transition_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    resumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    crashed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    snapshots: Mapped[List["Snapshot"]] = relationship(
        "Snapshot",
        back_populates="actor",
        lazy="selectin",
        foreign_keys="Snapshot.actor_id",
    )
    telemetry: Mapped[List["ActorTelemetry"]] = relationship(
        "ActorTelemetry",
        back_populates="actor",
        lazy="selectin",
        foreign_keys="ActorTelemetry.actor_id",
    )

    # Indexes
    __table_args__ = (
        Index("ix_actor_atespace_template", "atespace", "template_namespace", "template_name"),
        Index("ix_actor_status_node", "status", "node_id"),
    )

    def __repr__(self) -> str:
        return f"<Actor(uid={self.uid}, name={self.name}, status={self.status})>"

    def can_transition_to(self, new_status: ActorStatus) -> tuple[bool, str]:
        """Check if transition to new_status is valid."""
        valid_transitions = {
            ActorStatus.SUSPENDED: [ActorStatus.RUNNING],
            ActorStatus.RUNNING: [ActorStatus.PAUSED, ActorStatus.SUSPENDED, ActorStatus.CRASHED],
            ActorStatus.PAUSED: [ActorStatus.RUNNING, ActorStatus.SUSPENDED, ActorStatus.CRASHED],
            ActorStatus.CRASHED: [ActorStatus.SUSPENDED],
        }
        allowed = valid_transitions.get(self.status, [])
        if new_status in allowed:
            return True, ""
        return False, f"Invalid transition from {self.status.value} to {new_status.value}"

    def transition_to(self, new_status: ActorStatus) -> None:
        """Perform state transition with timestamp updates."""
        now = datetime.now(UTC)
        self.status = new_status
        self.last_transition_at = now
        self.updated_at = now

        if new_status == ActorStatus.RUNNING:
            self.resumed_at = now
        elif new_status == ActorStatus.PAUSED:
            self.paused_at = now
        elif new_status == ActorStatus.SUSPENDED:
            self.suspended_at = now
        elif new_status == ActorStatus.CRASHED:
            self.crashed_at = now