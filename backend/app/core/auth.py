"""Authentication dependencies and OIDC integration."""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings
from .database import get_db
from .security import verify_token, TokenData
# from ..models.user import User  # Moved inside function to avoid circular import
from ..services.user import get_user_by_email, create_user_from_oidc


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.oidc_issuer_url}/protocol/openid-connect/auth",
    tokenUrl=f"{settings.oidc_issuer_url}/protocol/openid-connect/token",
    refreshUrl=f"{settings.oidc_issuer_url}/protocol/openid-connect/token",
    scopes={
        "openid": "OpenID Connect",
        "profile": "Profile information",
        "email": "Email address",
        "roles": "User roles",
    },
    auto_error=False,
)


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> "User":
    """Get current authenticated user from token."""
    from ..models.user import User  # Local import to avoid circular dependency
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check required scopes
    if security_scopes.scopes:
        user_roles = set(token_data.roles)
        required = set(security_scopes.scopes)
        if not required.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
                headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
            )

    # Get or create user from DB
    user = await get_user_by_email(db, token_data.email or token_data.sub)
    if not user and token_data.email:
        user = await create_user_from_oidc(db, token_data.email, token_data.sub, token_data.roles)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Get current active user (alias for clarity)."""
    return current_user
def require_roles(*roles: str):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: "User" = Depends(get_current_active_user)) -> "User":
        user_roles = set(current_user.roles or [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return current_user
    return role_checker


# Role constants
ROLE_VIEWER = "viewer"
ROLE_OPERATOR = "operator"
ROLE_ADMIN = "admin"

ALL_ROLES = [ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN]