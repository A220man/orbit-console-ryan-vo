"""Actor service - core domain logic for actor lifecycle management."""

from datetime import datetime, UTC
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.actor import Actor, ActorStatus, SnapshotScope
from ..models.snapshot import Snapshot, SnapshotType
from ..models.telemetry import TelemetryMetric
from .telemetry import record_actor_metric


# Valid state transitions
VALID_TRANSITIONS: Dict[ActorStatus, List[ActorStatus]] = {
    ActorStatus.SUSPENDED: [ActorStatus.RUNNING],
    ActorStatus.RUNNING: [ActorStatus.PAUSED, ActorStatus.SUSPENDED, ActorStatus.CRASHED],
    ActorStatus.PAUSED: [ActorStatus.RUNNING, ActorStatus.SUSPENDED, ActorStatus.CRASHED],
    ActorStatus.CRASHED: [ActorStatus.SUSPENDED],
}


async def create_actor(
    db: AsyncSession,
    uid: str,
    name: str,
    atespace: str,
    template_namespace: str,
    template_name: str,
    container_name: str = "main",
    snapshot_scope: SnapshotScope = SnapshotScope.DATA,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
) -> Actor:
    """Create a new actor in SUSPENDED state."""
    actor = Actor(
        uid=uid,
        name=name,
        atespace=atespace,
        template_namespace=template_namespace,
        template_name=template_name,
        container_name=container_name,
        snapshot_scope=snapshot_scope,
        status=ActorStatus.SUSPENDED,
        labels=labels or {},
        annotations=annotations or {},
    )
    db.add(actor)
    await db.flush()
    await db.refresh(actor)

    # Record actor creation metric
    await record_actor_metric(
        db,
        template_namespace=template_namespace,
        template_name=template_name,
        container_name=container_name,
        metric_name="ate.actors.created",
        metric_type="counter",
        value=1.0,
    )

    return actor


async def get_actor(db: AsyncSession, actor_id: int) -> Optional[Actor]:
    """Get actor by ID with relationships."""
    result = await db.execute(
        select(Actor).options(selectinload(Actor.snapshots)).where(Actor.id == actor_id)
    )
    return result.scalar_one_or_none()


async def get_actor_by_uid(db: AsyncSession, uid: str) -> Optional[Actor]:
    """Get actor by UID with relationships."""
    result = await db.execute(
        select(Actor).options(selectinload(Actor.snapshots)).where(Actor.uid == uid)
    )
    return result.scalar_one_or_none()


async def list_actors(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ActorStatus] = None,
    atespace: Optional[str] = None,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Tuple[List[Actor], int]:
    """List actors with filtering and pagination."""
    query = select(Actor)
    count_query = select(func.count(Actor.id))

    conditions = []
    if status:
        conditions.append(Actor.status == status)
    if atespace:
        conditions.append(Actor.atespace == atespace)
    if template_namespace:
        conditions.append(Actor.template_namespace == template_namespace)
    if template_name:
        conditions.append(Actor.template_name == template_name)
    if node_id:
        conditions.append(Actor.node_id == node_id)

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    query = query.order_by(Actor.updated_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    actors = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return list(actors), total


async def update_actor(
    db: AsyncSession,
    actor_id: int,
    name: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    snapshot_scope: Optional[SnapshotScope] = None,
) -> Optional[Actor]:
    """Update actor metadata."""
    actor = await get_actor(db, actor_id)
    if not actor:
        return None

    if name is not None:
        actor.name = name
    if labels is not None:
        actor.labels = labels
    if annotations is not None:
        actor.annotations = annotations
    if snapshot_scope is not None:
        # Can only change scope when suspended
        if actor.status != ActorStatus.SUSPENDED:
            raise ValueError("Can only change snapshot scope when actor is SUSPENDED")
        actor.snapshot_scope = snapshot_scope

    actor.updated_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(actor)
    return actor


async def delete_actor(db: AsyncSession, actor_id: int) -> bool:
    """Delete an actor (only if not RUNNING)."""
    actor = await get_actor(db, actor_id)
    if not actor:
        return False

    if actor.status == ActorStatus.RUNNING:
        raise ValueError("Cannot delete RUNNING actor. Pause or suspend first.")

    await db.delete(actor)
    await db.flush()
    return True


async def transition_actor_state(
    db: AsyncSession,
    actor_id: int,
    new_status: ActorStatus,
    force: bool = False,
) -> Actor:
    """Transition actor to new state with validation."""
    actor = await get_actor(db, actor_id)
    if not actor:
        raise ValueError(f"Actor {actor_id} not found")

    # Validate transition (allow force for revert/dump operations)
    allowed = VALID_TRANSITIONS.get(actor.status, [])
    if new_status not in allowed and not force:
        raise ValueError(f"Invalid transition from {actor.status.value} to {new_status.value}")

    old_status = actor.status
    actor.transition_to(new_status)

    # Update telemetry counters (skip for no-op transitions)
    if old_status != new_status:
        await _update_status_metrics(db, actor, old_status, new_status)

    await db.flush()
    await db.refresh(actor)
    return actor


async def _update_status_metrics(
    db: AsyncSession,
    actor: Actor,
    old_status: ActorStatus,
    new_status: ActorStatus,
) -> None:
    """Update actor status gauge metrics."""
    # Decrement old status
    await record_actor_metric(
        db,
        template_namespace=actor.template_namespace,
        template_name=actor.template_name,
        container_name=actor.container_name,
        metric_name="ate.actors",
        metric_type="gauge",
        value=-1.0,
        labels={"status": old_status.value.lower()},
    )

    # Increment new status
    await record_actor_metric(
        db,
        template_namespace=actor.template_namespace,
        template_name=actor.template_name,
        container_name=actor.container_name,
        metric_name="ate.actors",
        metric_type="gauge",
        value=1.0,
        labels={"status": new_status.value.lower()},
    )

    # Record transition
    await record_actor_metric(
        db,
        template_namespace=actor.template_namespace,
        template_name=actor.template_name,
        container_name=actor.container_name,
        metric_name="ate.actor.transitions",
        metric_type="counter",
        value=1.0,
        labels={"from": old_status.value.lower(), "to": new_status.value.lower()},
    )


async def pause_actor(
    db: AsyncSession,
    actor_id: int,
    timer_seconds: Optional[int] = None,
    snapshot_scope: Optional[SnapshotScope] = None,
) -> Actor:
    """Pause actor (RUNNING -> PAUSED). Creates local snapshot."""
    actor = await transition_actor_state(db, actor_id, ActorStatus.PAUSED)

    # Create pause snapshot
    scope = snapshot_scope or actor.snapshot_scope
    snapshot = Snapshot(
        actor_id=actor.id,
        actor_uid=actor.uid,
        snapshot_type=SnapshotType.PAUSE,
        scope=scope.value,
        storage_path=f"/var/ate/snapshots/{actor.uid}/pause-{datetime.now(UTC).isoformat()}",
        size_bytes=0,  # Will be updated by ateom
        metadata={"timer_seconds": timer_seconds} if timer_seconds else {},
    )
    db.add(snapshot)
    await db.flush()

    actor.paused_snapshot_id = snapshot.id
    await db.flush()
    await db.refresh(actor)

    return actor


async def resume_actor(
    db: AsyncSession,
    actor_id: int,
    node_id: Optional[str] = None,
    worker_id: Optional[str] = None,
) -> Actor:
    """Resume actor (PAUSED/SUSPENDED -> RUNNING)."""
    actor = await transition_actor_state(db, actor_id, ActorStatus.RUNNING)

    if node_id:
        actor.node_id = node_id
    if worker_id:
        actor.worker_id = worker_id

    await db.flush()
    await db.refresh(actor)
    return actor


async def commit_actor(
    db: AsyncSession,
    actor_id: int,
    tag: Optional[str] = None,
    snapshot_scope: Optional[SnapshotScope] = None,
) -> Actor:
    """Commit actor (RUNNING -> SUSPENDED). Creates durable snapshot."""
    actor = await get_actor(db, actor_id)
    if not actor:
        raise ValueError(f"Actor {actor_id} not found")

    if actor.status not in [ActorStatus.RUNNING, ActorStatus.PAUSED]:
        raise ValueError(f"Can only commit from RUNNING or PAUSED, not {actor.status.value}")

    # Validate scope: onCommit must be subset of onPause
    scope = snapshot_scope or actor.snapshot_scope
    if actor.status == ActorStatus.PAUSED and scope == SnapshotScope.FULL and actor.snapshot_scope == SnapshotScope.DATA:
        raise ValueError("onCommit scope cannot be broader than onPause scope")

    actor = await transition_actor_state(db, actor_id, ActorStatus.SUSPENDED)

    # Create commit snapshot
    snapshot = Snapshot(
        actor_id=actor.id,
        actor_uid=actor.uid,
        snapshot_type=SnapshotType.COMMIT,
        scope=scope.value,
        tag=tag,
        storage_path=f"/var/ate/snapshots/{actor.uid}/commit-{datetime.now(UTC).isoformat()}",
        size_bytes=0,
        metadata={},
    )
    if tag:
        snapshot.metadata["tag"] = tag

    db.add(snapshot)
    await db.flush()

    actor.latest_snapshot_id = snapshot.id
    if actor.status == ActorStatus.PAUSED:
        actor.paused_snapshot_id = None

    await db.flush()
    await db.refresh(actor)

    return actor


async def revert_actor(
    db: AsyncSession,
    actor_id: int,
    tag: Optional[str] = None,
    snapshot_id: Optional[int] = None,
) -> Actor:
    """Revert actor to a previous snapshot (any state -> SUSPENDED)."""
    actor = await get_actor(db, actor_id)
    if not actor:
        raise ValueError(f"Actor {actor_id} not found")

    # Find target snapshot
    if snapshot_id:
        snapshot = await db.get(Snapshot, snapshot_id)
        if not snapshot or snapshot.actor_id != actor.id:
            raise ValueError("Snapshot not found")
    elif tag:
        result = await db.execute(
            select(Snapshot).where(
                and_(Snapshot.actor_id == actor.id, Snapshot.tag == tag)
            ).order_by(Snapshot.created_at.desc())
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise ValueError(f"Tag '{tag}' not found")
    else:
        # Revert to latest commit
        result = await db.execute(
            select(Snapshot).where(
                and_(Snapshot.actor_id == actor.id, Snapshot.snapshot_type == SnapshotType.COMMIT)
            ).order_by(Snapshot.created_at.desc())
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise ValueError("No commit snapshot found")

    # Transition to SUSPENDED (force for revert from SUSPENDED)
    actor = await transition_actor_state(db, actor_id, ActorStatus.SUSPENDED, force=True)

    # Create revert snapshot
    revert_snapshot = Snapshot(
        actor_id=actor.id,
        actor_uid=actor.uid,
        snapshot_type=SnapshotType.REVERT,
        scope=snapshot.scope,
        tag=tag,
        storage_path=snapshot.storage_path,
        size_bytes=snapshot.size_bytes,
        checksum=snapshot.checksum,
        oci_image_digest=snapshot.oci_image_digest,
        gvisor_version=snapshot.gvisor_version,
        metadata={"reverted_from": snapshot.id},
    )
    db.add(revert_snapshot)
    await db.flush()

    actor.latest_snapshot_id = revert_snapshot.id
    await db.flush()
    await db.refresh(actor)

    return actor


async def dump_actor(
    db: AsyncSession,
    actor_id: int,
    tag: str,
) -> Actor:
    """Dump crashed actor filesystem state (CRASHED -> SUSPENDED)."""
    actor = await get_actor(db, actor_id)
    if not actor:
        raise ValueError(f"Actor {actor_id} not found")

    if actor.status != ActorStatus.CRASHED:
        raise ValueError("Can only dump CRASHED actors")

    # Transition to SUSPENDED (force for dump from CRASHED)
    actor = await transition_actor_state(db, actor_id, ActorStatus.SUSPENDED, force=True)

    # Create dump snapshot (filesystem only, no memory)
    snapshot = Snapshot(
        actor_id=actor.id,
        actor_uid=actor.uid,
        snapshot_type=SnapshotType.DUMP,
        scope=SnapshotScope.DATA.value,  # Dumps are always data-only
        tag=tag,
        storage_path=f"/var/ate/snapshots/{actor.uid}/dump-{datetime.now(UTC).isoformat()}",
        size_bytes=0,
        metadata={"dumped_from_crashed": True},
    )
    db.add(snapshot)
    await db.flush()

    actor.latest_snapshot_id = snapshot.id
    await db.flush()
    await db.refresh(actor)

    return actor


async def get_actor_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get aggregate actor statistics."""
    # Total count
    total_result = await db.execute(select(func.count(Actor.id)))
    total = total_result.scalar_one()

    # Count by status
    status_counts = {}
    for status in ActorStatus:
        result = await db.execute(
            select(func.count(Actor.id)).where(Actor.status == status)
        )
        status_counts[status.value.lower()] = result.scalar_one()

    # Count by template
    template_result = await db.execute(
        select(
            Actor.template_namespace,
            Actor.template_name,
            func.count(Actor.id).label("count")
        ).group_by(Actor.template_namespace, Actor.template_name)
    )
    templates = [
        {"namespace": row.template_namespace, "name": row.template_name, "count": row.count}
        for row in template_result.all()
    ]

    return {
        "total": total,
        "by_status": status_counts,
        "by_template": templates,
    }


async def get_actor_count_by_status(
    db: AsyncSession,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
) -> Dict[str, int]:
    """Get actor count grouped by status (for ate.actors gauge)."""
    query = select(Actor.status, func.count(Actor.id)).group_by(Actor.status)

    conditions = []
    if template_namespace:
        conditions.append(Actor.template_namespace == template_namespace)
    if template_name:
        conditions.append(Actor.template_name == template_name)

    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    return {row.status.value.lower(): row[1] for row in result.all()}


async def get_crash_count(
    db: AsyncSession,
    template_namespace: Optional[str] = None,
    template_name: Optional[str] = None,
) -> int:
    """Get count of actors in CRASHED state (for ate.actor.crashes metric)."""
    query = select(func.count(Actor.id)).where(Actor.status == ActorStatus.CRASHED)

    conditions = []
    if template_namespace:
        conditions.append(Actor.template_namespace == template_namespace)
    if template_name:
        conditions.append(Actor.template_name == template_name)

    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    return result.scalar_one() or 0