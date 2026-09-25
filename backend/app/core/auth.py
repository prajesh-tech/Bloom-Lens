import secrets
from typing import Optional, List, Callable
from dataclasses import dataclass
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logging import logger

# Header and Bearer schemes for API authentication
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer_auth = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    """Represents the authenticated principal with role information for authorization."""
    user_id: str
    role: str = "instructor"


async def get_current_user(
    header_key: Optional[str] = Security(_api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(_bearer_auth),
) -> AuthenticatedUser:
    """
    FastAPI dependency for authenticating incoming API requests.
    Validates against configured settings.API_KEY using constant-time comparison.
    Supports both `X-API-Key` header and `Authorization: Bearer <API_KEY>`.
    Returns 401 Unauthorized for missing or invalid credentials.
    """
    # If auth is disabled (e.g. local dev toggle), return a default authenticated user
    if not settings.AUTH_ENABLED:
        return AuthenticatedUser(user_id="dev_user", role="admin")

    configured_key = settings.API_KEY
    if not configured_key or not configured_key.strip():
        # If AUTH_ENABLED is True but no API_KEY is set in settings, reject requests safely
        logger.error("Authentication is enabled but API_KEY is not configured.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Server API key is not configured.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    provided_key: Optional[str] = None
    if header_key:
        provided_key = header_key.strip()
    elif bearer_creds and bearer_creds.credentials:
        provided_key = bearer_creds.credentials.strip()

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials. Provide X-API-Key header or Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to prevent timing side-channel attacks
    if not secrets.compare_digest(provided_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(user_id="api_key_user", role="instructor")


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Role-based authorization dependency factory.
    Keeps authorization decoupled from authentication.
    """
    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {', '.join(allowed_roles)}.",
            )
        return current_user

    return role_checker
