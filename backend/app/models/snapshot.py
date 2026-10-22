"""Snapshot model for actor state persistence."""

import enum
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Boolean, Text, JSON, Integer, Enum as SQLEnum, ForeignKey, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from ..core.database import Base


class SnapshotType(str, enum.Enum):
    """Type of snapshot."""
    PAUSE = "pause"      # Created on pause
    COMMIT = "commit"    # Created on commit
    REVERT = "revert"    # Created on revert
    DUMP = "dump"        # Created on dump from CRASHED


class Snapshot(Base):
    """Snapshot of actor state."""

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("actors.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_uid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # Snapshot identification
    snapshot_type: Mapped[SnapshotType] = mapped_column(SQLEnum(SnapshotType), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)  # "full" or "data"
    tag: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Storage info
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Metadata
    oci_image_digest: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gvisor_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    snapshot_metadata: Mapped[Dict[str, Any]] = mapped_column(SQLiteJSON, default=dict, nullable=False)

    # State
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validation_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    actor: Mapped["Actor"] = relationship(
        "Actor",
        back_populates="snapshots",
        foreign_keys="Snapshot.actor_id",
    )

    # Indexes
    __table_args__ = (
        Index("ix_snapshot_actor_type", "actor_id", "snapshot_type"),
        Index("ix_snapshot_actor_tag", "actor_id", "tag"),
    )

    def __repr__(self) -> str:
        return f"<Snapshot(id={self.id}, actor={self.actor_uid}, type={self.snapshot_type}, tag={self.tag})>"