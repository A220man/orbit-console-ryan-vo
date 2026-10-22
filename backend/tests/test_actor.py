"""Actor model and service tests."""

import pytest
from datetime import UTC
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.actor import Actor, ActorStatus, SnapshotScope
from app.models.snapshot import Snapshot, SnapshotType
from app.services.actor import (
    create_actor,
    get_actor,
    get_actor_by_uid,
    list_actors,
    transition_actor_state,
    pause_actor,
    resume_actor,
    commit_actor,
    revert_actor,
    dump_actor,
    get_actor_count_by_status,
    get_crash_count,
)


@pytest.mark.asyncio
async def test_create_actor(test_session: AsyncSession):
    """Test actor creation."""
    actor = await create_actor(
        test_session,
        uid="test-actor-001",
        name="Test Actor",
        atespace="default",
        template_namespace="default",
        template_name="test-template",
        container_name="main",
        snapshot_scope=SnapshotScope.DATA,
    )

    assert actor.id is not None
    assert actor.uid == "test-actor-001"
    assert actor.name == "Test Actor"
    assert actor.status == ActorStatus.SUSPENDED
    assert actor.snapshot_scope == SnapshotScope.DATA


@pytest.mark.asyncio
async def test_get_actor(test_session: AsyncSession):
    """Test getting actor by ID and UID."""
    actor = await create_actor(
        test_session,
        uid="test-actor-002",
        name="Test Actor 2",
        atespace="default",
        template_namespace="default",
        template_name="test-template",
    )

    found = await get_actor(test_session, actor.id)
    assert found is not None
    assert found.uid == actor.uid

    found = await get_actor_by_uid(test_session, actor.uid)
    assert found is not None
    assert found.id == actor.id


@pytest.mark.asyncio
async def test_list_actors(test_session: AsyncSession):
    """Test listing actors with filters."""
    await create_actor(
        test_session,
        uid="actor-1",
        name="Actor 1",
        atespace="space-a",
        template_namespace="ns1",
        template_name="template-a",
    )
    await create_actor(
        test_session,
        uid="actor-2",
        name="Actor 2",
        atespace="space-b",
        template_namespace="ns1",
        template_name="template-b",
    )
    await create_actor(
        test_session,
        uid="actor-3",
        name="Actor 3",
        atespace="space-a",
        template_namespace="ns2",
        template_name="template-a",
    )

    actors, total = await list_actors(test_session)
    assert total == 3

    actors, total = await list_actors(test_session, atespace="space-a")
    assert total == 2
    assert all(a.atespace == "space-a" for a in actors)

    actors, total = await list_actors(test_session, template_namespace="ns1")
    assert total == 2


@pytest.mark.asyncio
async def test_state_transitions(test_session: AsyncSession):
    """Test valid and invalid state transitions."""
    actor = await create_actor(
        test_session,
        uid="transition-test",
        name="Transition Test",
        atespace="default",
        template_namespace="default",
        template_name="test",
    )

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    assert actor.status == ActorStatus.RUNNING

    actor = await pause_actor(test_session, actor.id)
    assert actor.status == ActorStatus.PAUSED

    actor = await resume_actor(test_session, actor.id)
    assert actor.status == ActorStatus.RUNNING

    actor = await commit_actor(test_session, actor.id)
    assert actor.status == ActorStatus.SUSPENDED

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    assert actor.status == ActorStatus.RUNNING

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.CRASHED)
    assert actor.status == ActorStatus.CRASHED

    actor = await dump_actor(test_session, actor.id, tag="dumped")
    assert actor.status == ActorStatus.SUSPENDED


@pytest.mark.asyncio
async def test_invalid_transition(test_session: AsyncSession):
    """Test invalid state transition raises error."""
    actor = await create_actor(
        test_session,
        uid="invalid-transition",
        name="Invalid Transition",
        atespace="default",
        template_namespace="default",
        template_name="test",
    )

    with pytest.raises(ValueError, match="Invalid transition"):
        await transition_actor_state(test_session, actor.id, ActorStatus.PAUSED)


@pytest.mark.asyncio
async def test_pause_actor(test_session: AsyncSession):
    """Test pausing an actor creates snapshot."""
    actor = await create_actor(
        test_session,
        uid="pause-test",
        name="Pause Test",
        atespace="default",
        template_namespace="default",
        template_name="test",
    )

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    actor = await pause_actor(test_session, actor.id, timer_seconds=300)

    assert actor.status == ActorStatus.PAUSED
    assert actor.paused_snapshot_id is not None

    snapshot = await test_session.get(Snapshot, actor.paused_snapshot_id)
    assert snapshot is not None
    assert snapshot.snapshot_type == SnapshotType.PAUSE


@pytest.mark.asyncio
async def test_commit_actor(test_session: AsyncSession):
    """Test committing an actor."""
    actor = await create_actor(
        test_session,
        uid="commit-test",
        name="Commit Test",
        atespace="default",
        template_namespace="default",
        template_name="test",
    )

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    actor = await commit_actor(test_session, actor.id, tag="v1.0")

    assert actor.status == ActorStatus.SUSPENDED
    assert actor.latest_snapshot_id is not None

    snapshot = await test_session.get(Snapshot, actor.latest_snapshot_id)
    assert snapshot is not None
    assert snapshot.snapshot_type == SnapshotType.COMMIT
    assert snapshot.tag == "v1.0"


@pytest.mark.asyncio
async def test_revert_actor(test_session: AsyncSession):
    """Test reverting an actor."""
    actor = await create_actor(
        test_session,
        uid="revert-test",
        name="Revert Test",
        atespace="default",
        template_namespace="default",
        template_name="test",
    )

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    actor = await commit_actor(test_session, actor.id, tag="checkpoint-1")
    commit_snapshot_id = actor.latest_snapshot_id

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    actor = await commit_actor(test_session, actor.id, tag="checkpoint-2")

    actor = await revert_actor(test_session, actor.id, tag="checkpoint-1")
    assert actor.status == ActorStatus.SUSPENDED

    revert_snapshot = await test_session.get(Snapshot, actor.latest_snapshot_id)
    assert revert_snapshot is not None
    assert revert_snapshot.snapshot_type == SnapshotType.REVERT
    assert revert_snapshot.metadata.get("reverted_from") == commit_snapshot_id


@pytest.mark.asyncio
async def test_dump_actor(test_session: AsyncSession):
    """Test dumping a crashed actor."""
    actor = await create_actor(
        test_session,
        uid="dump-test",
        name="Dump Test",
        atespace="default",
        template_namespace="default",
        template_name="test",
    )

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    actor = await transition_actor_state(test_session, actor.id, ActorStatus.CRASHED)

    actor = await dump_actor(test_session, actor.id, tag="crash-dump")
    assert actor.status == ActorStatus.SUSPENDED

    snapshot = await test_session.get(Snapshot, actor.latest_snapshot_id)
    assert snapshot is not None
    assert snapshot.snapshot_type == SnapshotType.DUMP
    assert snapshot.scope == SnapshotScope.DATA.value
    assert snapshot.metadata.get("dumped_from_crashed") is True


@pytest.mark.asyncio
async def test_actor_count_by_status(test_session: AsyncSession):
    """Test actor count by status aggregation."""
    await create_actor(test_session, uid="a1", name="A1", atespace="s", template_namespace="ns", template_name="t")
    await create_actor(test_session, uid="a2", name="A2", atespace="s", template_namespace="ns", template_name="t")
    await create_actor(test_session, uid="a3", name="A3", atespace="s", template_namespace="ns", template_name="t")

    actors, _ = await list_actors(test_session)
    await transition_actor_state(test_session, actors[1].id, ActorStatus.RUNNING)
    await transition_actor_state(test_session, actors[2].id, ActorStatus.RUNNING)
    await transition_actor_state(test_session, actors[2].id, ActorStatus.CRASHED)

    counts = await get_actor_count_by_status(test_session, "ns", "t")
    assert counts.get("suspended", 0) == 1
    assert counts.get("running", 0) == 1
    assert counts.get("crashed", 0) == 1
    assert counts.get("paused", 0) == 0


@pytest.mark.asyncio
async def test_crash_count(test_session: AsyncSession):
    """Test crash count."""
    await create_actor(test_session, uid="c1", name="C1", atespace="s", template_namespace="ns", template_name="t")
    await create_actor(test_session, uid="c2", name="C2", atespace="s", template_namespace="ns", template_name="t")

    actors, _ = await list_actors(test_session)
    await transition_actor_state(test_session, actors[0].id, ActorStatus.RUNNING)
    await transition_actor_state(test_session, actors[0].id, ActorStatus.CRASHED)

    count = await get_crash_count(test_session, "ns", "t")
    assert count == 1


@pytest.mark.asyncio
async def test_snapshot_scope_validation(test_session: AsyncSession):
    """Test onCommit subset of onPause validation."""
    actor = await create_actor(
        test_session,
        uid="scope-test",
        name="Scope Test",
        atespace="default",
        template_namespace="default",
        template_name="test",
        snapshot_scope=SnapshotScope.DATA,
    )

    actor = await transition_actor_state(test_session, actor.id, ActorStatus.RUNNING)
    actor = await pause_actor(test_session, actor.id, snapshot_scope=SnapshotScope.DATA)

    with pytest.raises(ValueError, match="onCommit scope cannot be broader"):
        await commit_actor(test_session, actor.id, snapshot_scope=SnapshotScope.FULL)

    actor = await commit_actor(test_session, actor.id, snapshot_scope=SnapshotScope.DATA)
    assert actor.status == ActorStatus.SUSPENDED