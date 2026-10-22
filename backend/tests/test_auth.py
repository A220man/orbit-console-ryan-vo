"""Authentication and authorization tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user import create_user_from_oidc
from app.core.security import create_access_token, verify_token
from app.core.auth import ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN


@pytest.mark.asyncio
async def test_create_access_token():
    """Test JWT token creation."""
    token = create_access_token(
        subject="test-user",
        email="test@example.com",
        roles=["viewer"],
    )

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

    # Verify token
    token_data = verify_token(token)
    assert token_data is not None
    assert token_data.sub == "test-user"
    assert token_data.email == "test@example.com"
    assert token_data.roles == ["viewer"]


@pytest.mark.asyncio
async def test_invalid_token():
    """Test invalid token verification."""
    token_data = verify_token("invalid-token")
    assert token_data is None


@pytest.mark.asyncio
async def test_user_creation(test_session: AsyncSession):
    """Test user creation from OIDC."""
    user = await create_user_from_oidc(
        test_session,
        email="newuser@example.com",
        subject="oidc-sub-123",
        roles=["viewer"],
        name="New User",
    )

    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.subject == "oidc-sub-123"
    assert user.roles == ["viewer"]
    assert user.is_active is True


@pytest.mark.asyncio
async def test_role_hierarchy():
    """Test role definitions."""
    assert ROLE_VIEWER == "viewer"
    assert ROLE_OPERATOR == "operator"
    assert ROLE_ADMIN == "admin"


@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client: AsyncClient):
    """Test that protected endpoints require authentication."""
    response = await client.get("/api/v1/actors")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_with_insufficient_scope(client: AsyncClient, test_session: AsyncSession):
    """Test token with insufficient roles."""
    # Create user with viewer role only
    user = await create_user_from_oidc(
        test_session,
        email="viewer@example.com",
        subject="viewer-sub",
        roles=["viewer"],
    )

    token = create_access_token(
        subject=user.subject,
        email=user.email,
        roles=user.roles,
    )

    # Try to access operator endpoint
    response = await client.post(
        "/api/v1/actors",
        json={
            "uid": "test-actor",
            "name": "Test Actor",
            "atespace": "default",
            "template_namespace": "default",
            "template_name": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_operator_can_create_actor(client: AsyncClient, test_session: AsyncSession):
    """Test operator can create actor."""
    user = await create_user_from_oidc(
        test_session,
        email="operator@example.com",
        subject="operator-sub",
        roles=["operator"],
    )

    token = create_access_token(
        subject=user.subject,
        email=user.email,
        roles=user.roles,
    )

    response = await client.post(
        "/api/v1/actors",
        json={
            "uid": "operator-actor",
            "name": "Operator Actor",
            "atespace": "default",
            "template_namespace": "default",
            "template_name": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_admin_can_delete_actor(client: AsyncClient, test_session: AsyncSession):
    """Test admin can delete actor."""
    # Create actor first
    user = await create_user_from_oidc(
        test_session,
        email="admin@example.com",
        subject="admin-sub",
        roles=["admin"],
    )

    token = create_access_token(
        subject=user.subject,
        email=user.email,
        roles=user.roles,
    )

    # Create actor
    create_resp = await client.post(
        "/api/v1/actors",
        json={
            "uid": "delete-test",
            "name": "Delete Test",
            "atespace": "default",
            "template_namespace": "default",
            "template_name": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    actor_id = create_resp.json()["id"]

    # Delete actor
    delete_resp = await client.delete(
        f"/api/v1/actors/{actor_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204