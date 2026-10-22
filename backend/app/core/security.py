"""Security utilities for JWT and password handling."""

from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from pydantic import BaseModel

from .config import settings


class TokenData(BaseModel):
    """Decoded token data."""
    sub: str
    email: Optional[str] = None
    roles: list[str] = []
    exp: int
    iat: int
    nonce: Optional[str] = None


def create_access_token(
    subject: str,
    email: Optional[str] = None,
    roles: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None,
    nonce: Optional[str] = None,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    if email:
        to_encode["email"] = email
    if roles:
        to_encode["roles"] = roles
    if nonce:
        to_encode["nonce"] = nonce

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=None,  # We validate audience in the auth layer
        )
        return TokenData(**payload)
    except JWTError:
        return None


def decode_token_unverified(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without verification (for debugging)."""
    try:
        return jwt.get_unverified_claims(token)
    except JWTError:
        return None