"""Authentication endpoints - OIDC/PKCE flow."""

from typing import Optional
from datetime import datetime, UTC
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
import secrets
import urllib.parse

from ..core.config import settings
from ..core.auth import oauth2_scheme, get_current_active_user, ROLE_VIEWER
from ..core.security import create_access_token
from ..services.user import get_user_by_email, create_user_from_oidc, update_last_login
from ..models.user import User
from ..core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class TokenResponse(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """User info response."""
    sub: str
    email: str
    name: Optional[str] = None
    roles: list[str]


# In-memory state store for PKCE (use Redis in production)
_pkce_store: dict[str, dict] = {}


@router.get("/login")
async def login(
    redirect_uri: Optional[str] = None,
    prompt: Optional[str] = None,
) -> RedirectResponse:
    """Initiate OIDC authorization code flow with PKCE."""
    # Generate PKCE parameters
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = code_verifier  # S256 would be hash, but we'll use plain for demo

    # Generate state
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    # Store PKCE data
    _pkce_store[state] = {
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "nonce": nonce,
        "redirect_uri": redirect_uri or settings.oidc_redirect_uri,
        "created_at": datetime.now(UTC).isoformat(),
    }

    # Build authorization URL
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": settings.oidc_scopes,
        "redirect_uri": redirect_uri or settings.oidc_redirect_uri,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "plain",  # Use S256 in production
    }

    if prompt:
        params["prompt"] = prompt

    auth_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle OIDC callback."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC error: {error} - {error_description}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state",
        )

    # Retrieve PKCE data
    pkce_data = _pkce_store.pop(state, None)
    if not pkce_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state",
        )

    # In production: exchange code for tokens at token endpoint
    # For demo, we'll simulate successful authentication
    # Real implementation would:
    # 1. POST to token endpoint with code, code_verifier, client_id, client_secret
    # 2. Validate ID token (signature, issuer, audience, nonce)
    # 3. Extract claims

    # Simulated user info from ID token
    user_info = {
        "sub": f"oidc-user-{secrets.token_hex(8)}",
        "email": "user@example.com",
        "name": "Demo User",
        "roles": [ROLE_VIEWER],
    }

    # Get or create user
    user = await get_user_by_email(db, user_info["email"])
    if not user:
        user = await create_user_from_oidc(
            db,
            email=user_info["email"],
            subject=user_info["sub"],
            roles=user_info["roles"],
            name=user_info["name"],
        )

    await update_last_login(db, user.id)

    # Create access token
    access_token = create_access_token(
        subject=user.subject,
        email=user.email,
        roles=user.roles,
        nonce=pkce_data["nonce"],
    )

    # Redirect to frontend with token
    frontend_url = pkce_data["redirect_uri"].replace("/callback", "")
    redirect_url = f"{frontend_url}?token={access_token}"
    return RedirectResponse(url=redirect_url)


@router.post("/token", response_model=TokenResponse)
async def token_exchange(
    grant_type: str,
    code: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    code_verifier: Optional[str] = None,
    refresh_token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Token endpoint for authorization code exchange."""
    if grant_type == "authorization_code":
        if not code or not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing code or code_verifier",
            )

        # In production: verify code_verifier against stored challenge
        # For demo, accept any valid-looking code
        if not code.startswith("auth-code-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code",
            )

        # Simulate user lookup
        user = await get_user_by_email(db, "user@example.com")
        if not user:
            user = await create_user_from_oidc(
                db,
                email="user@example.com",
                subject="demo-subject",
                roles=[ROLE_VIEWER],
            )

        access_token = create_access_token(
            subject=user.subject,
            email=user.email,
            roles=user.roles,
        )

        return TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing refresh_token",
            )
        # In production: validate refresh token and issue new access token
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Refresh token not implemented",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: {grant_type}",
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserInfo:
    """Get current user info."""
    return UserInfo(
        sub=current_user.subject,
        email=current_user.email,
        name=current_user.name,
        roles=current_user.roles,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Logout endpoint (client should discard token)."""
    # In production: revoke refresh token, notify Keycloak
    return {"message": "Logged out successfully"}


@router.get("/config")
async def get_oidc_config() -> dict:
    """Get OIDC configuration for frontend."""
    return {
        "issuer": settings.oidc_issuer_url,
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "scopes": settings.oidc_scopes.split(),
    }