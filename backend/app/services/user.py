"""User service."""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_by_email(db: AsyncSession, email: str) -> Optional["User"]:
    """Get user by email."""
    from ..models.user import User
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_subject(db: AsyncSession, subject: str) -> Optional["User"]:
    """Get user by OIDC subject."""
    from ..models.user import User
    result = await db.execute(select(User).where(User.subject == subject))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional["User"]:
    """Get user by ID."""
    from ..models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user_from_oidc(
    db: AsyncSession,
    email: str,
    subject: str,
    roles: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> "User":
    """Create user from OIDC claims."""
    from ..models.user import User
    user = User(
        subject=subject,
        email=email,
        name=name,
        roles=roles or ["viewer"],
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user_roles(db: AsyncSession, user_id: int, roles: List[str]) -> Optional["User"]:
    """Update user roles."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.roles = roles
    await db.flush()
    await db.refresh(user)
    return user


async def update_last_login(db: AsyncSession, user_id: int) -> None:
    """Update user's last login timestamp."""
    from datetime import datetime, UTC
    user = await get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.now(UTC)
        await db.flush()