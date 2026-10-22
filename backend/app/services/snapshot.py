"""Snapshot service."""

from typing import Optional, List, Tuple
from datetime import datetime, UTC
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.snapshot import Snapshot, SnapshotType
from ..models.actor import Actor


async def create_snapshot(
    db: AsyncSession,
    actor_id: int,
    snapshot_type: SnapshotType,
    scope: str,
    storage_path: str,
    tag: Optional[str] = None,
    size_bytes: int = 0,
    checksum: Optional[str] = None,
    oci_image_digest: Optional[str] = None,
    gvisor_version: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Snapshot:
    """Create a new snapshot record."""
    actor = await db.get(Actor, actor_id)
    if not actor:
        raise ValueError(f"Actor {actor_id} not found")

    snapshot = Snapshot(
        actor_id=actor_id,
        actor_uid=actor.uid,
        snapshot_type=snapshot_type,
        scope=scope,
        tag=tag,
        storage_path=storage_path,
        size_bytes=size_bytes,
        checksum=checksum,
        oci_image_digest=oci_image_digest,
        gvisor_version=gvisor_version,
        metadata=metadata or {},
    )
    db.add(snapshot)
    await db.flush()
    await db.refresh(snapshot)
    return snapshot


async def get_snapshot(db: AsyncSession, snapshot_id: int) -> Optional[Snapshot]:
    """Get snapshot by ID."""
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    return result.scalar_one_or_none()


async def list_snapshots(
    db: AsyncSession,
    actor_id: Optional[int] = None,
    actor_uid: Optional[str] = None,
    snapshot_type: Optional[SnapshotType] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[Snapshot], int]:
    """List snapshots with filtering."""
    query = select(Snapshot)
    count_query = select(func.count(Snapshot.id))

    conditions = []
    if actor_id:
        conditions.append(Snapshot.actor_id == actor_id)
    if actor_uid:
        conditions.append(Snapshot.actor_uid == actor_uid)
    if snapshot_type:
        conditions.append(Snapshot.snapshot_type == snapshot_type)
    if tag:
        conditions.append(Snapshot.tag == tag)

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    query = query.order_by(Snapshot.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    snapshots = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return list(snapshots), total


async def validate_snapshot(db: AsyncSession, snapshot_id: int) -> Tuple[bool, Optional[str]]:
    """Validate snapshot integrity (checksum, existence)."""
    snapshot = await get_snapshot(db, snapshot_id)
    if not snapshot:
        return False, "Snapshot not found"

    if not snapshot.is_valid:
        return False, snapshot.validation_error or "Snapshot marked invalid"

    # In real implementation, would verify checksum against storage
    # For now, assume valid if marked valid
    return True, None


async def get_latest_snapshot(
    db: AsyncSession,
    actor_id: int,
    snapshot_type: Optional[SnapshotType] = None,
) -> Optional[Snapshot]:
    """Get latest snapshot for an actor."""
    query = select(Snapshot).where(Snapshot.actor_id == actor_id)
    if snapshot_type:
        query = query.where(Snapshot.snapshot_type == snapshot_type)
    query = query.order_by(Snapshot.created_at.desc()).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_snapshots_by_tag(
    db: AsyncSession,
    actor_id: int,
    tag: str,
) -> List[Snapshot]:
    """Get all snapshots with a given tag for an actor."""
    result = await db.execute(
        select(Snapshot).where(
            and_(Snapshot.actor_id == actor_id, Snapshot.tag == tag)
        ).order_by(Snapshot.created_at.desc())
    )
    return list(result.scalars().all())