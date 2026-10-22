"""API integration tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user import create_user_from_oidc
from app.core.security import create_access_token
from app.core.auth import ROLE_OPERATOR, ROLE_ADMIN
from app.models.actor import ActorStatus, SnapshotScope


@pytest.mark.asyncio
async def test_full_actor_lifecycle(client: AsyncClient, test_session: AsyncSession):
    """Test complete actor lifecycle via API."""
    # Create operator user
    user = await create_user_from_oidc(
        test_session,
        email="lifecycle@example.com",
        subject="lifecycle-sub",
        roles=["operator"],
    )
    token = create_access_token(subject=user.subject, email=user.email, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create actor
    create_resp = await client.post(
        "/api/v1/actors",
        json={
            "uid": "lifecycle-actor",
            "name": "Lifecycle Actor",
            "atespace": "production",
            "template_namespace": "default",
            "template_name": "worker-v1",
            "container_name": "main",
            "snapshot_scope": "data",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    actor = create_resp.json()
    actor_id = actor["id"]
    assert actor["status"] == "SUSPENDED"
    assert actor["uid"] == "lifecycle-actor"

    # 2. List actors
    list_resp = await client.get("/api/v1/actors", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1

    # 3. Get actor by ID
    get_resp = await client.get(f"/api/v1/actors/{actor_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["uid"] == "lifecycle-actor"

    # 4. Resume actor (SUSPENDED -> RUNNING)
    resume_resp = await client.post(
        f"/api/v1/actors/{actor_id}/resume",
        headers=headers,
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "RUNNING"

    # 5. Pause actor (RUNNING -> PAUSED)
    pause_resp = await client.post(
        f"/api/v1/actors/{actor_id}/pause",
        json={"timer_seconds": 300},
        headers=headers,
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "PAUSED"

    # 6. Resume again (PAUSED -> RUNNING)
    resume_resp = await client.post(
        f"/api/v1/actors/{actor_id}/resume",
        headers=headers,
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "RUNNING"

    # 7. Commit actor (RUNNING -> SUSPENDED)
    commit_resp = await client.post(
        f"/api/v1/actors/{actor_id}/commit",
        json={"tag": "checkpoint-1"},
        headers=headers,
    )
    assert commit_resp.status_code == 200
    assert commit_resp.json()["status"] == "SUSPENDED"

    # 8. Resume and crash
    resume_resp = await client.post(f"/api/v1/actors/{actor_id}/resume", headers=headers)
    assert resume_resp.json()["status"] == "RUNNING"

    # Direct transition to CRASHED (simulating node failure)
    from app.services.actor import transition_actor_state
    await transition_actor_state(test_session, actor_id, ActorStatus.CRASHED)

    # 9. Dump crashed actor (CRASHED -> SUSPENDED)
    dump_resp = await client.post(
        f"/api/v1/actors/{actor_id}/dump",
        json={"tag": "crash-dump"},
        headers=headers,
    )
    assert dump_resp.status_code == 200
    assert dump_resp.json()["status"] == "SUSPENDED"

    # 10. List snapshots
    snapshots_resp = await client.get(f"/api/v1/actors/{actor_id}/snapshots", headers=headers)
    assert snapshots_resp.status_code == 200
    snapshots = snapshots_resp.json()
    assert len(snapshots) >= 3  # pause, commit, dump


@pytest.mark.asyncio
async def test_actor_filtering(client: AsyncClient, test_session: AsyncSession):
    """Test actor listing with filters."""
    user = await create_user_from_oidc(
        test_session,
        email="filter@example.com",
        subject="filter-sub",
        roles=["operator"],
    )
    token = create_access_token(subject=user.subject, email=user.email, roles=user.roles)
    headers = {"Authorization": f"Bearer {token}"}

    # Create actors with different attributes
    await client.post("/api/v1/actors", json={
        "uid": "filter-a1", "name": "A1", "atespace": "space-1",
        "template_namespace": "ns1", "template_name": "tmpl-1"
    }, headers=headers)
    await client.post("/api/v1/actors", json={
        "uid": "filter-a2", "name": "A2", "atespace": "space-2",
        "template_namespace": "ns1", "template_name": "tmpl-2"
    }, headers=headers)
    await client.post("/api/v1/actors", json={
        "uid": "filter-a3", "name": "A3", "atespace": "space-1",
        "template_namespace": "ns2", "template_name": "tmpl-1"
    }, headers=headers)

    # Filter by atespace
    resp = await client.get("/api/v1/actors?atespace=space-1", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(a["atespace"] == "space-1" for a in data["actors"])

    # Filter by template namespace
    resp = await client.get("/api/v1/actors?template_namespace=ns1", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2

    # Filter by status
    actors, _ = await list_actors(test_session)
    from app.services.actor import transition_actor_state
    await transition_actor_state(test_session, actors[0].id, ActorStatus.RUNNING)

    resp = await client.get("/api/v1/actors?status=RUNNING", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(a["status"] == "RUNNING" for a in data["actors"])


# Import needed for test
from app.services.actor import list_actors, transition_actor_state