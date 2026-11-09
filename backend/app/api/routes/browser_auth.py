import asyncio
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user, AuthenticatedUser
from app.core.browser_sessions import COOKIE_NAME, hash_password, verify_password, token_digest
from app.core.config import settings
from app.core.database import get_db
from app.core.upload_limits import UploadLimiter
from app.models.reviewer import Reviewer, ReviewerSession
from app.schemas.reviewer import LoginRequest, SessionResponse


def public_login() -> None:
    """Intentionally public credential exchange; registration is unavailable."""


router = APIRouter(prefix='/auth', tags=['Browser sessions'])
login_limiter = UploadLimiter()
dummy_hash = hash_password('not-a-real-reviewer-password')


@router.post('/login', response_model=SessionResponse, dependencies=[Depends(public_login)])
async def login(payload: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    login_limiter.check(request.client.host if request.client else 'unknown', settings.LOGIN_RATE_LIMIT_PER_MINUTE)
    user = (await db.execute(select(Reviewer).where(Reviewer.username == payload.username))).scalar_one_or_none()
    user_id, role, enabled, password_hash = (user.id, user.role, user.enabled, user.password_hash) if user else (None, None, False, dummy_hash)
    await db.rollback()
    valid = await asyncio.to_thread(verify_password, payload.password, password_hash)
    if not valid or not enabled:
        raise HTTPException(401, 'Invalid username or password.')
    token, csrf = secrets.token_urlsafe(32), secrets.token_hex(32)
    db.add(ReviewerSession(token_hash=token_digest(token), reviewer_id=user_id, csrf_token=csrf,
                           expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_TTL_HOURS)))
    await db.commit()
    response.set_cookie(COOKIE_NAME, token, httponly=True, secure=settings.SESSION_COOKIE_SECURE,
                        samesite='lax', max_age=settings.SESSION_TTL_HOURS * 3600, path='/')
    return SessionResponse(user_id=f'reviewer:{user_id}:{payload.username}', role=role, csrf_token=csrf)


@router.get('/me', response_model=SessionResponse)
async def current_session(request: Request, user: AuthenticatedUser = Depends(get_current_user)):
    session = getattr(request.state, 'browser_session', None)
    return SessionResponse(user_id=user.user_id, role=user.role, csrf_token=session.csrf_token if session else None)


@router.post('/logout', status_code=204)
async def logout(request: Request, response: Response, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = getattr(request.state, 'browser_session', None)
    if session:
        await db.delete(session)
        await db.commit()
    response.delete_cookie(COOKIE_NAME, path='/', secure=settings.SESSION_COOKIE_SECURE, httponly=True, samesite='lax')
