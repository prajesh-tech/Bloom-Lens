import hashlib
import secrets
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.reviewer import Reviewer, ReviewerSession

COOKIE_NAME = 'bloomlens_session'


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f'scrypt${salt}${digest}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split('$')
        if algorithm != 'scrypt':
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        return secrets.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def resolve_browser_session(request: Request, db: AsyncSession):
    token = request.cookies.get(COOKIE_NAME)
    if not token or len(token) > 256:
        raise HTTPException(401, 'Authentication required.')
    session = await db.get(ReviewerSession, token_digest(token))
    now = datetime.now(timezone.utc)
    if session is None or session.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(401, 'Session expired or revoked.')
    user = await db.get(Reviewer, session.reviewer_id)
    if user is None or not user.enabled:
        raise HTTPException(401, 'Session expired or revoked.')
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        csrf = request.headers.get('X-CSRF-Token', '')
        origin = request.headers.get('Origin')
        own_origin = str(request.base_url).rstrip('/')
        if (not secrets.compare_digest(csrf, session.csrf_token)
                or (origin and origin not in {*settings.cors_origins, own_origin})):
            raise HTTPException(403, 'CSRF validation failed.')
    request.state.browser_session = session
    return user
